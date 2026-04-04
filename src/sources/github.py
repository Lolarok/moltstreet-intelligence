"""
MoltStreet Intelligence — GitHub Source
Commit activity + stars for protocol repos.
"""
import os
import time
from . import fetch_json


def get_github_activity(repo: str) -> dict | None:
    """Fetch GitHub activity for a repo.
    Returns {commits_4w, stars} or None.
    """
    if not repo:
        return None

    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"User-Agent": "MoltStreet/3.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Commit activity (last 4 weeks)
    commits_data = fetch_json(
        f"https://api.github.com/repos/{repo}/stats/commit_activity",
        headers=headers,
    )

    # Repo info
    repo_data = fetch_json(
        f"https://api.github.com/repos/{repo}",
        headers=headers,
    )

    commits_4w = 0
    if commits_data and isinstance(commits_data, list):
        commits_4w = sum(w.get("total", 0) for w in commits_data[-4:])

    stars = 0
    if repo_data and isinstance(repo_data, dict):
        stars = repo_data.get("stargazers_count", 0)

    return {"commits_4w": commits_4w, "stars": stars}


def get_all_github_activity(repos: dict, delay: float = 0.5) -> dict:
    """Fetch GitHub activity for multiple repos.
    repos: {symbol: repo_path}
    Returns {symbol: {commits_4w, stars}}.
    """
    results = {}
    for sym, repo in repos.items():
        if not repo:
            continue
        data = get_github_activity(repo)
        if data:
            results[sym] = data
        time.sleep(delay)  # Respect rate limits
    return results
