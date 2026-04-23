#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from common import read_json, write_json


def summarize_text(text: str, category: str) -> str:
    body = " ".join(text.split())
    short = body[:160] + ("..." if len(body) > 160 else "")
    return f"[{category}] {short}" if short else f"[{category}] (summary unavailable)"


def fetch_preview(url: str) -> dict:
    result = {"title": "", "description": "", "image": "", "domain": urlparse(url).netloc.lower()}
    if not url:
        return result
    try:
        req = Request(url, headers={"User-Agent": "x-offsec-bot/0.1"}, method="GET")
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        def meta(prop: str, name: str = "property") -> str:
            pattern = rf'<meta[^>]+{name}=[\"\']{re.escape(prop)}[\"\'][^>]+content=[\"\']([^\"\']*)[\"\']'
            m = re.search(pattern, html, re.IGNORECASE)
            return (m.group(1) if m else "").strip()

        title = meta("og:title")
        if not title:
            t = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            title = t.group(1).strip() if t else ""

        desc = meta("og:description")
        if not desc:
            desc = meta("description", name="name")
        image = meta("og:image")
        result.update({"title": title[:160], "description": desc[:280], "image": image})
    except (URLError, TimeoutError, ValueError):
        pass
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach preview metadata and summaries")
    parser.add_argument("--in", dest="input_path", type=Path, default=Path("data/daily/ranked_latest.json"))
    parser.add_argument("--out", type=Path, default=Path("data/daily/final_latest.json"))
    parser.add_argument("--max-preview", type=int, default=20)
    args = parser.parse_args()

    payload = read_json(args.input_path, default={"items": []})
    items = payload.get("items", [])

    for idx, item in enumerate(items):
        url = (item.get("external_urls") or [""])[0]
        item["preview"] = fetch_preview(url) if idx < args.max_preview else {"title": "", "description": "", "image": "", "domain": ""}
        item["summary"] = summarize_text(item.get("text", ""), item.get("category", "Tool"))

    out = {
        "generated_at": payload.get("generated_at"),
        "count": len(items),
        "items": items,
    }
    write_json(args.out, out)
    print(f"Summarized {len(items)} posts -> {args.out}")


if __name__ == "__main__":
    main()
