#!/usr/bin/env python3
"""
Collect commit-time and language stats across all repos via the GitHub REST
API and write data/stats.json.

With GH_TOKEN (a PAT with `repo` scope) private and org repos are included;
without it only public repos are counted (and the 60 req/h limit applies).
Only commits authored by USERNAME count, so bot commits are ignored.
"""
import collections
import datetime
import json
import os
import sys
from zoneinfo import ZoneInfo

import requests

USERNAME = os.environ.get("GH_PROFILE_USER", "SpaceEnergy")
TZ = ZoneInfo(os.environ.get("TIME_ZONE", "Europe/Berlin"))
TOKEN = os.environ.get("GH_TOKEN")
EXCLUDE_LANGS = {l.strip() for l in os.environ.get("EXCLUDE_LANGS", "").split(",") if l.strip()}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_PATH = os.path.join(ROOT, "data", "stats.json")

S = requests.Session()
S.headers["Accept"] = "application/vnd.github+json"
if TOKEN:
    S.headers["Authorization"] = f"Bearer {TOKEN}"


def get_all(url, **params):
    params.setdefault("per_page", 100)
    while url:
        r = S.get(url, params=params, timeout=30)
        if r.status_code == 409:  # empty repository
            return
        r.raise_for_status()
        yield from r.json()
        url, params = r.links.get("next", {}).get("url"), None


def list_repos():
    if TOKEN:
        repos = get_all("https://api.github.com/user/repos",
                        affiliation="owner,collaborator,organization_member")
    else:
        repos = get_all(f"https://api.github.com/users/{USERNAME}/repos", type="owner")
    return [r for r in repos if not r["fork"]]


def main():
    user = S.get(f"https://api.github.com/users/{USERNAME}", timeout=30).json()
    repos = list_repos()

    hours = [0] * 24
    weekdays = [0] * 7  # Monday = 0
    langs = collections.Counter()
    lang_repos = collections.Counter()
    total = 0
    stars = 0

    for repo in repos:
        name = repo["full_name"]
        owned = repo["owner"]["login"].lower() == USERNAME.lower()
        n = 0
        for c in get_all(f"https://api.github.com/repos/{name}/commits", author=USERNAME):
            when = datetime.datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
            local = when.astimezone(TZ)
            hours[local.hour] += 1
            weekdays[local.weekday()] += 1
            n += 1
        total += n
        # count languages/stars for repos you own or actually committed to,
        # skipping this profile repo (its python scripts would skew the stats)
        if (owned or n) and repo["name"].lower() != USERNAME.lower():
            stars += repo["stargazers_count"] if owned else 0
            repo_langs = S.get(f"https://api.github.com/repos/{name}/languages", timeout=30).json()
            for lang, size in repo_langs.items():
                if lang not in EXCLUDE_LANGS:
                    langs[lang] += size
                    lang_repos[lang] += 1
        print(f"{name}: {n} commits", file=sys.stderr)

    data = {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "time_zone": str(TZ),
        "total_commits": total,
        "repos": sum(1 for r in repos if r["owner"]["login"].lower() == USERNAME.lower()),
        "stars": stars,
        "followers": user.get("followers", 0),
        "member_since": user.get("created_at", "")[:4],
        "hours": hours,
        "weekdays": weekdays,
        "languages": [{"name": k, "bytes": v, "repos": lang_repos[k]} for k, v in langs.most_common()],
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=1)
    print(f"wrote {OUT_PATH}: {total} commits in {len(repos)} repos")


if __name__ == "__main__":
    main()
