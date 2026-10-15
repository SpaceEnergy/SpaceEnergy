#!/usr/bin/env python3
"""
Collect commit-time and language stats across all repos via the GitHub REST
API and write data/stats.json.

Covers your own repos and all repos of the orgs you belong to. With GH_TOKEN
(a PAT with `repo` + `read:org` scope) private repos and private org
memberships are included; without it only public ones are counted (and the
60 req/h limit applies).
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
        if r.status_code in (403, 404, 409) and "/commits" in url and "rate limit" not in r.text:
            # empty repo, or an org repo the token may not read: skip it
            print(f"skipping {url}: {r.status_code}", file=sys.stderr)
            return
        r.raise_for_status()
        yield from r.json()
        url, params = r.links.get("next", {}).get("url"), None


def list_repos():
    """Own repos plus every repo of every org you belong to, deduplicated."""
    # public org memberships always count, even if the token lacks read:org
    orgs = list(get_all(f"https://api.github.com/users/{USERNAME}/orgs"))
    if TOKEN:
        repos = list(get_all("https://api.github.com/user/repos",
                             affiliation="owner,collaborator,organization_member"))
        try:
            orgs += get_all("https://api.github.com/user/orgs")
        except requests.HTTPError as e:
            print(f"can't list private org memberships: {e}", file=sys.stderr)
    else:
        repos = list(get_all(f"https://api.github.com/users/{USERNAME}/repos", type="owner"))
    org_names = list(dict.fromkeys(o["login"] for o in orgs))
    for org in org_names:
        repos += get_all(f"https://api.github.com/orgs/{org}/repos", type="all")
    unique = {r["full_name"]: r for r in repos if not r["fork"]}
    return list(unique.values()), org_names


def repo_summary(repo, commits):
    return {
        "name": repo["name"],
        "owner": repo["owner"]["login"],
        "description": repo.get("description") or "",
        "language": repo.get("language") or "",
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "commits": commits,
        "pushed_at": repo.get("pushed_at") or "",
    }


def collapse(text):
    return " ".join(text.split())


def fetch_activity(limit=8):
    """Recent public events, with runs of the same action on one repo merged."""
    r = S.get(f"https://api.github.com/users/{USERNAME}/events/public", params={"per_page": 100}, timeout=30)
    if not r.ok:
        return []
    out = []
    for e in sorted(r.json(), key=lambda e: e["created_at"], reverse=True):
        p, repo = e["payload"], e["repo"]["name"]
        t = e["type"]
        if t == "PushEvent":
            kind, text = "push", f'pushed to {p.get("ref", "").removeprefix("refs/heads/")}'
        elif t == "ReleaseEvent" and p.get("action") == "published":
            rel = p["release"]
            kind, text = "release", f'released {rel.get("name") or rel.get("tag_name", "")}'
        elif t == "PullRequestEvent" and p.get("action") in ("opened", "closed"):
            pr = p["pull_request"]
            verb = "merged" if pr.get("merged") else p["action"]
            title = pr.get("title")
            kind, text = "pr", f'{verb} PR #{p["number"]}' + (f": {title}" if title else "")
        elif t == "IssuesEvent" and p.get("action") in ("opened", "closed"):
            title = p["issue"].get("title")
            kind, text = "issue", f'{p["action"]} issue #{p["issue"]["number"]}' + (f": {title}" if title else "")
        elif t == "IssueCommentEvent":
            kind, text = "comment", f'commented on #{p["issue"]["number"]}'
        elif t == "CreateEvent" and p.get("ref_type") == "repository":
            kind, text = "create", "created repository"
        elif t == "PublicEvent":
            kind, text = "create", "made repository public"
        elif t == "WatchEvent":
            kind, text = "star", "starred"
        elif t == "ForkEvent":
            kind, text = "fork", "forked"
        else:
            continue
        prev = out[-1] if out else None
        if prev and prev["kind"] == kind and prev["repo"] == repo and kind in ("push", "comment", "issue", "star"):
            prev["count"] += 1
            if kind == "comment":
                prev["text"] = "commented on issues"
            elif kind == "issue":
                prev["text"] = f'{p["action"]} issues'
            continue
        if len(out) == limit:
            break
        out.append({"kind": kind, "repo": repo, "text": collapse(text), "at": e["created_at"], "count": 1})
    return out


def main():
    user = S.get(f"https://api.github.com/users/{USERNAME}", timeout=30).json()
    repos, orgs = list_repos()

    hours = [0] * 24
    weekdays = [0] * 7  # Monday = 0
    langs = collections.Counter()
    lang_repos = collections.Counter()
    total = 0
    stars = 0
    contributed = 0
    top_repos = []

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
        if not (owned or n):
            continue
        # repos/stars/languages count for repos you own or actually committed to
        contributed += 1
        stars += repo["stargazers_count"]
        if not repo["private"]:  # never show private repo names on the profile
            top_repos.append(repo_summary(repo, n))
        # skip this profile repo for languages (its python scripts would skew them)
        if repo["name"].lower() != USERNAME.lower():
            r = S.get(f"https://api.github.com/repos/{name}/languages", timeout=30)
            for lang, size in (r.json() if r.ok else {}).items():
                if lang not in EXCLUDE_LANGS:
                    langs[lang] += size
                    lang_repos[lang] += 1
        print(f"{name}: {n} commits", file=sys.stderr)

    data = {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "time_zone": str(TZ),
        "total_commits": total,
        "repos": contributed,
        "orgs": orgs,
        "stars": stars,
        "followers": user.get("followers", 0),
        "member_since": user.get("created_at", "")[:4],
        "hours": hours,
        "weekdays": weekdays,
        "languages": [{"name": k, "bytes": v, "repos": lang_repos[k]} for k, v in langs.most_common()],
        "top_repos": sorted(top_repos, key=lambda r: (r["stars"], r["commits"]), reverse=True)[:6],
        "activity": fetch_activity(),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=1)
    print(f"wrote {OUT_PATH}: {total} commits in {len(repos)} repos")


if __name__ == "__main__":
    main()
