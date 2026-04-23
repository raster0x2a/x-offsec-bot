#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from common import Post, extract_urls, read_json, utc_now_iso, write_json

RECENT_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"
DEFAULT_QUERY = "(red team OR pentest OR exploit OR cve OR bug bounty OR writeup) lang:en -is:retweet"


def fetch_from_x(token: str, query: str, max_results: int) -> list[Post]:
    params = {
        "query": query,
        "max_results": max(10, min(max_results, 100)),
        "tweet.fields": "author_id,created_at,entities",
        "expansions": "author_id",
        "user.fields": "username",
    }
    req = Request(
        f"{RECENT_SEARCH_URL}?{urlencode(params)}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    users = {u["id"]: u.get("username", u["id"]) for u in payload.get("includes", {}).get("users", [])}
    posts: list[Post] = []
    for row in payload.get("data", []):
        urls = [u.get("expanded_url") for u in row.get("entities", {}).get("urls", []) if u.get("expanded_url")]
        if not urls:
            urls = extract_urls(row.get("text", ""))
        author = users.get(row.get("author_id", ""), row.get("author_id", "unknown"))
        post_id = row["id"]
        posts.append(
            Post(
                post_id=post_id,
                text=row.get("text", ""),
                author=author,
                created_at=row.get("created_at", utc_now_iso()),
                post_url=f"https://x.com/{author}/status/{post_id}",
                external_urls=urls,
            )
        )
    return posts


def fetch_mock() -> list[Post]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return [
        Post(
            post_id="mock-1",
            text="New AD attack path research with PoC https://example.com/ad-research",
            author="offsec_researcher",
            created_at=now,
            post_url="https://x.com/offsec_researcher/status/mock-1",
            external_urls=["https://example.com/ad-research"],
        ),
        Post(
            post_id="mock-2",
            text="CVE writeup and mitigation notes https://example.org/cve-writeup",
            author="sec_news",
            created_at=now,
            post_url="https://x.com/sec_news/status/mock-2",
            external_urls=["https://example.org/cve-writeup"],
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect X posts and save raw dataset")
    parser.add_argument("--query", default=os.getenv("X_QUERY", DEFAULT_QUERY))
    parser.add_argument("--max-results", type=int, default=int(os.getenv("MAX_RESULTS", "50")))
    parser.add_argument("--out", type=Path, default=Path("data/daily/raw_latest.json"))
    args = parser.parse_args()

    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if token:
        posts = fetch_from_x(token=token, query=args.query, max_results=args.max_results)
        mode = "x_api"
    else:
        posts = fetch_mock()
        mode = "mock"

    payload = {
        "generated_at": utc_now_iso(),
        "mode": mode,
        "query": args.query,
        "count": len(posts),
        "items": [p.to_dict() for p in posts],
    }

    write_json(args.out, payload)
    print(f"Collected {len(posts)} posts in {mode} mode -> {args.out}")


if __name__ == "__main__":
    main()
