#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import extract_urls, normalize_url, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize raw collected posts")
    parser.add_argument("--in", dest="input_path", type=Path, default=Path("data/daily/raw_latest.json"))
    parser.add_argument("--out", type=Path, default=Path("data/daily/normalized_latest.json"))
    args = parser.parse_args()

    payload = read_json(args.input_path, default={"items": []})
    items = payload.get("items", [])

    normalized_items = []
    for item in items:
        urls = item.get("external_urls") or extract_urls(item.get("text", ""))
        norm_urls = [normalize_url(u) for u in urls if u]
        item["external_urls"] = sorted(list(dict.fromkeys(norm_urls)))
        item["text"] = " ".join(item.get("text", "").split())
        normalized_items.append(item)

    out = {
        "generated_at": payload.get("generated_at"),
        "mode": payload.get("mode", "unknown"),
        "count": len(normalized_items),
        "items": normalized_items,
    }
    write_json(args.out, out)
    print(f"Normalized {len(normalized_items)} posts -> {args.out}")


if __name__ == "__main__":
    main()
