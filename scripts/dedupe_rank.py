#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse

from common import read_json, write_json

DEFAULT_RULES = {
    "trusted_domains": {},
    "blocked_keywords": [],
    "preferred_authors": {},
    "category_bias": {"Tool": 1.0, "Blog/Writeup": 1.0, "News/Advisory": 1.0},
}


def classify(text: str, urls: list[str]) -> str:
    t = f"{text} {' '.join(urls)}".lower()
    if any(k in t for k in ["cve", "advisory", "incident", "vuln"]):
        return "News/Advisory"
    if any(k in t for k in ["writeup", "research", "analysis", "blog"]):
        return "Blog/Writeup"
    return "Tool"


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def score_item(item: dict, rules: dict) -> float:
    text = item.get("text", "").lower()
    urls = item.get("external_urls", [])
    cat = item.get("category", "Tool")

    s = 1.0
    if urls:
        d = domain(urls[0])
        s += float(rules.get("trusted_domains", {}).get(d, 0))
    s += float(rules.get("preferred_authors", {}).get(item.get("author", ""), 0))
    if any(k.lower() in text for k in rules.get("blocked_keywords", [])):
        s -= 2.0
    s *= float(rules.get("category_bias", {}).get(cat, 1.0))

    created = item.get("created_at")
    if created:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
            s += max(0, 1 - age_hours / 24)
        except ValueError:
            pass
    return round(s, 4)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dedupe, classify, and rank posts")
    parser.add_argument("--in", dest="input_path", type=Path, default=Path("data/daily/normalized_latest.json"))
    parser.add_argument("--rules", type=Path, default=Path("data/config/feedback_rules.json"))
    parser.add_argument("--out", type=Path, default=Path("data/daily/ranked_latest.json"))
    parser.add_argument("--top-n", type=int, default=30)
    args = parser.parse_args()

    payload = read_json(args.input_path, default={"items": []})
    rules = read_json(args.rules, default=DEFAULT_RULES)

    deduped: list[dict] = []
    seen_url = set()
    similar_buckets = defaultdict(list)

    for item in payload.get("items", []):
        urls = item.get("external_urls", [])
        primary_url = urls[0] if urls else ""
        if primary_url and primary_url in seen_url:
            continue

        text = item.get("text", "")
        similar_hit = False
        for prev in deduped:
            if similarity(text, prev.get("text", "")) >= 0.92:
                similar_hit = True
                similar_buckets[prev.get("post_id")].append(item.get("post_id"))
                break
        if similar_hit:
            continue

        if primary_url:
            seen_url.add(primary_url)

        item["category"] = classify(text, urls)
        item["score"] = score_item(item, rules)
        deduped.append(item)

    ranked = sorted(deduped, key=lambda x: x.get("score", 0), reverse=True)[: args.top_n]
    out = {
        "generated_at": payload.get("generated_at"),
        "count": len(ranked),
        "clusters": {k: v for k, v in similar_buckets.items() if v},
        "items": ranked,
    }

    write_json(args.out, out)
    print(f"Ranked {len(ranked)} posts -> {args.out}")


if __name__ == "__main__":
    main()
