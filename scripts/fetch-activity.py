#!/usr/bin/env python3
"""Fetch GitHub activity for radaiko and write data/activity.json.

Requires a GitHub token with `repo` + `read:user` scopes (classic PAT)
or repository access to private repos (fine-grained PAT) to include
private repository activity.  The token is read from the ACTIVITY_TOKEN
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


def fetch_all_repos(token):
    """Fetch all repos accessible to the authenticated user (includes private)."""
    all_repos = []
    page_num = 1
    while True:
        try:
            # /user/repos returns private repos; /users/{name}/repos does NOT
            repos = api_get(
                f"/user/repos?per_page=100&page={page_num}&affiliation=owner,collaborator",
                token,
            )
            if not repos:
                break
            all_repos.extend(repos)
            if len(repos) < 100:
                break
            page_num += 1
        except HTTPError:
            break
    return all_repos


def fetch_repo_commits(token, repo_full_name, since_iso):
    """Fetch commits authored by GITHUB_USER in a repo since cutoff."""
    all_commits = []
    page_num = 1
    while True:
        try:
            commits = api_get(
                f"/repos/{repo_full_name}/commits"
                f"?since={since_iso}&author={GITHUB_USER}"
                f"&per_page=100&page={page_num}",
                token,
            )
            if not commits:
                break
            all_commits.extend(commits)
            if len(commits) < 100:
                break
            page_num += 1
        except HTTPError:
            break
    return all_commits


def fetch_public_events(token):
    """Fallback: fetch up to 300 recent public events."""
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

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(weeks=WEEKS)
    cutoff_iso = cutoff.isoformat()
    week_seconds = 7 * 24 * 60 * 60

    repos = {}
    weekly_commits = [0] * WEEKS
    pages_sites = []

    if token:
        # Authenticated path: fetch all repos (including private) and their commits
        all_repos = fetch_all_repos(token)
        private_count = sum(1 for r in all_repos if r.get("private"))
        print(f"Found {len(all_repos)} repos ({private_count} private) via authenticated API")

        for repo_info in all_repos:
            full_name = repo_info["full_name"]
            short_name = repo_info["name"]
            owner = repo_info["owner"]["login"]

            # Discover GitHub Pages sites
            if repo_info.get("has_pages") and not repo_info.get("fork"):
                if short_name != f"{GITHUB_USER}.github.io":
                    pages_sites.append({
                        "name": short_name,
                        "url": f"https://{GITHUB_USER}.github.io/{short_name}/",
                        "description": repo_info.get("description") or "",
                        "language": repo_info.get("language") or "",
                    })

            # Fetch commits for this repo in the activity window
            commits = fetch_repo_commits(token, full_name, cutoff_iso)
            if not commits:
                continue

            last_activity = max(
                c["commit"]["author"]["date"] for c in commits
            )

            repos[full_name] = {
                "fullName": full_name,
                "name": short_name,
                "owner": owner,
                "isOwn": owner == GITHUB_USER,
                "commits": len(commits),
                "lastActivity": last_activity,
            }

            # Bucket commits into weeks
            for commit in commits:
                commit_date = datetime.fromisoformat(
                    commit["commit"]["author"]["date"].replace("Z", "+00:00")
                )
                age_seconds = (now - commit_date).total_seconds()
                week_index = int(age_seconds / week_seconds)
                if 0 <= week_index < WEEKS:
                    weekly_commits[WEEKS - 1 - week_index] += 1
    else:
        # Unauthenticated fallback: use public events API
        events = fetch_public_events(token)
        for event in events:
            if event.get("type") != "PushEvent":
                continue
            created = datetime.fromisoformat(
                event["created_at"].replace("Z", "+00:00")
            )
            if created < cutoff:
                continue
            repo_name = event["repo"]["name"]
            short_name = repo_name.split("/")[-1]
            owner = repo_name.split("/")[0]
            commit_count = len(event.get("payload", {}).get("commits", []))
            if commit_count == 0:
                commit_count = 1
            if repo_name not in repos:
                repos[repo_name] = {
                    "fullName": repo_name,
                    "name": short_name,
                    "owner": owner,
                    "isOwn": owner == GITHUB_USER,
                    "commits": 0,
                    "lastActivity": event["created_at"],
                }
            repos[repo_name]["commits"] += commit_count
            if event["created_at"] > repos[repo_name]["lastActivity"]:
                repos[repo_name]["lastActivity"] = event["created_at"]
            age_seconds = (now - created).total_seconds()
            week_index = int(age_seconds / week_seconds)
            if 0 <= week_index < WEEKS:
                weekly_commits[WEEKS - 1 - week_index] += commit_count

    # Sort repos by commit count descending
    sorted_repos = sorted(repos.values(), key=lambda r: r["commits"], reverse=True)
    total_commits = sum(weekly_commits)
    active_weeks = sum(1 for w in weekly_commits if w > 0)

    pages_sites.sort(key=lambda p: p["name"].lower())
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
