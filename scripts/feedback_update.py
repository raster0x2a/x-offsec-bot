#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from common import read_json, write_json

DEFAULT_RULES = {
    "trusted_domains": {},
    "blocked_keywords": [],
    "preferred_authors": {},
    "category_bias": {"Tool": 1.0, "Blog/Writeup": 1.0, "News/Advisory": 1.0},
}


def clamp(v: float, lo: float = -2.0, hi: float = 2.0) -> float:
    return max(lo, min(hi, v))


def main() -> None:
    parser = argparse.ArgumentParser(description="Update feedback rules from GitHub Issues labels")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument("--rules", type=Path, default=Path("data/config/feedback_rules.json"))
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token or not args.repo:
        print("Skip feedback update: GITHUB_TOKEN or repository is missing")
        write_json(args.rules, read_json(args.rules, default=DEFAULT_RULES))
        return

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{args.repo}/issues?state=closed&per_page=100&labels=feedback"
    req = Request(url, headers=headers, method="GET")
    with urlopen(req, timeout=20) as resp:
        issues = json.loads(resp.read().decode("utf-8"))

    rules = read_json(args.rules, default=DEFAULT_RULES)
    trusted_domains = rules.setdefault("trusted_domains", {})

    for issue in issues:
        labels = {lb["name"] for lb in issue.get("labels", [])}
        body = issue.get("body", "")
        domain = ""
        for line in body.splitlines():
            if line.lower().startswith("domain:"):
                domain = line.split(":", 1)[1].strip().lower()
                break
        if not domain:
            continue

        current = float(trusted_domains.get(domain, 0.0))
        if "good" in labels:
            current += 0.1
        if "noise" in labels:
            current -= 0.15
        trusted_domains[domain] = round(clamp(current), 3)

    write_json(args.rules, rules)
    print(f"Updated feedback rules -> {args.rules}")


if __name__ == "__main__":
    main()
