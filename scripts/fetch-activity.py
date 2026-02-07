#!/usr/bin/env python3
"""Fetch GitHub activity for radaiko and write data/activity.json.

Requires a GitHub token with `repo` + `read:user` scopes to include
private repository events.  The token is read from the GITHUB_TOKEN
environment variable.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

GITHUB_USER = "radaiko"
GITHUB_API = "https://api.github.com"
WEEKS = 12
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "activity.json")


def api_get(path, token):
    url = f"{GITHUB_API}{path}"
    req = Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_pages_sites(token):
    """Find all user repos that have GitHub Pages enabled."""
    pages = []
    page_num = 1
    while True:
        try:
            repos = api_get(
                f"/users/{GITHUB_USER}/repos?per_page=100&page={page_num}", token
            )
            if not repos:
                break
            for repo in repos:
                if repo.get("has_pages") and not repo.get("fork"):
                    name = repo["name"]
                    # The user's .github.io repo is the main site itself, skip it
                    if name == f"{GITHUB_USER}.github.io":
                        continue
                    pages.append({
                        "name": name,
                        "url": f"https://{GITHUB_USER}.github.io/{name}/",
                        "description": repo.get("description") or "",
                        "language": (repo.get("language") or ""),
                    })
            page_num += 1
        except HTTPError:
            break
    return sorted(pages, key=lambda p: p["name"].lower())


def fetch_events(token):
    """Fetch up to 300 recent events (3 pages of 100)."""
    all_events = []
    for page in range(1, 4):
        try:
            events = api_get(
                f"/users/{GITHUB_USER}/events?per_page=100&page={page}", token
            )
            if not events:
                break
            all_events.extend(events)
        except HTTPError:
            break
    return all_events


def main():
    token = os.environ.get("ACTIVITY_TOKEN", "")
    if not token:
        print("Warning: ACTIVITY_TOKEN not set, private repos won't be included",
              file=sys.stderr)

    events = fetch_events(token)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(weeks=WEEKS)
    week_ms = 7 * 24 * 60 * 60

    repos = {}
    weekly_commits = [0] * WEEKS

    for event in events:
        if event.get("type") != "PushEvent":
            continue

        created = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
        if created < cutoff:
            continue

        repo_name = event["repo"]["name"]  # "owner/repo"
        short_name = repo_name.split("/")[-1]
        owner = repo_name.split("/")[0]
        commits = len(event.get("payload", {}).get("commits", []))
        if commits == 0:
            commits = 1

        if repo_name not in repos:
            repos[repo_name] = {
                "fullName": repo_name,
                "name": short_name,
                "owner": owner,
                "isOwn": owner == GITHUB_USER,
                "commits": 0,
                "lastActivity": event["created_at"],
            }

        repos[repo_name]["commits"] += commits
        if event["created_at"] > repos[repo_name]["lastActivity"]:
            repos[repo_name]["lastActivity"] = event["created_at"]

        # Bucket into weeks
        age_seconds = (now - created).total_seconds()
        week_index = int(age_seconds / week_ms)
        if 0 <= week_index < WEEKS:
            weekly_commits[WEEKS - 1 - week_index] += commits

    # Sort repos by commit count descending
    sorted_repos = sorted(repos.values(), key=lambda r: r["commits"], reverse=True)

    total_commits = sum(weekly_commits)
    active_weeks = sum(1 for w in weekly_commits if w > 0)

    # Discover repos with GitHub Pages enabled
    pages_sites = fetch_pages_sites(token)
    print(f"Found {len(pages_sites)} repos with GitHub Pages enabled")

    output = {
        "generatedAt": now.isoformat(),
        "repos": sorted_repos,
        "weeklyCommits": weekly_commits,
        "totalCommits": total_commits,
        "activeWeeks": active_weeks,
        "pages": pages_sites,
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(sorted_repos)} repos, {total_commits} commits to {OUTPUT}")


if __name__ == "__main__":
    main()
