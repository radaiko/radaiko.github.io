# radaiko.github.io

Personal GitHub Pages site that serves as a portfolio and activity dashboard.

## Features

- Displays recent GitHub activity across all repositories
- Auto-updates via GitHub Actions workflow
- Clean, static HTML interface

## How It Works

A Python script (`scripts/fetch-activity.py`) runs on a schedule via GitHub Actions to fetch recent activity data and store it in `data/activity.json`. The `index.html` page renders this data in the browser.

## Tech Stack

- HTML/CSS/JavaScript
- Python (data fetching)
- GitHub Actions (automation)
