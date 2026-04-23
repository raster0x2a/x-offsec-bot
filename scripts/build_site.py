#!/usr/bin/env python3
from __future__ import annotations

import argparse
from html import escape
from datetime import datetime
from pathlib import Path

from common import JST, UTC, read_json, write_json


def to_jst(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(JST)
        return dt.strftime("%Y-%m-%d %H:%M JST")
    except Exception:
        return ""


def to_utc(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(UTC)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return ""


def render_html(items: list[dict], generated_at: str, date_key: str) -> str:
    cards = []
    for item in items:
        link = (item.get("external_urls") or [""])[0]
        preview = item.get("preview", {})
        title = preview.get("title") or link
        description = preview.get("description", "")
        cards.append(
            f"""
      <article class="card">
        <div class="chip">{escape(item.get("category", ""))}</div>
        <p class="meta muted">{escape(item.get("created_at_jst", ""))} ({escape(item.get("created_at_utc", ""))})</p>
        <h3><a href="{escape(link)}" target="_blank">{escape(title)}</a></h3>
        <p class="muted">{escape(description)}</p>
        <p>{escape(item.get("summary", ""))}</p>
        <p class="meta">source: <a href="{escape(item.get("post_url", ""))}" target="_blank">X post</a></p>
      </article>
            """.rstrip()
        )
    body = "\n".join(cards)
    return f"""<!doctype html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>X OffSec Daily Digest</title>
    <style>
      body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2rem auto; max-width: 1000px; padding: 0 1rem; background: #0b1020; color: #f5f7ff; }}
      .muted {{ color: #a9b1d6; }}
      .grid {{ display: grid; grid-template-columns: 1fr; gap: 1rem; }}
      .card {{ border: 1px solid #313a6b; border-radius: 12px; padding: 1rem; background: #141a33; }}
      .chip {{ display: inline-block; font-size: .8rem; padding: .2rem .5rem; border-radius: 999px; background: #23306d; }}
      a {{ color: #89b4ff; }}
      .meta {{ font-size: .85rem; }}
    </style>
  </head>
  <body>
    <h1>X OffSec Daily Digest</h1>
    <p class="muted">Generated: {escape(generated_at)} / Date: {escape(date_key)}</p>
    <div class="grid">
{body}
    </div>
  </body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GitHub Pages static site")
    parser.add_argument("--in", dest="input_path", type=Path, default=Path("data/daily/final_latest.json"))
    parser.add_argument("--out-html", type=Path, default=Path("docs/index.html"))
    parser.add_argument("--out-daily", type=Path, default=None)
    args = parser.parse_args()

    payload = read_json(args.input_path, default={"items": []})
    items = payload.get("items", [])

    for item in items:
        item["created_at_jst"] = to_jst(item.get("created_at", ""))
        item["created_at_utc"] = to_utc(item.get("created_at", ""))

    generated_at = payload.get("generated_at") or datetime.now(UTC).isoformat()
    date_key = generated_at[:10]

    if args.out_daily:
        daily_json = args.out_daily
    else:
        daily_json = Path(f"data/daily/{date_key}.json")
    write_json(daily_json, payload)

    html = render_html(items=items, generated_at=generated_at, date_key=date_key)

    args.out_html.parent.mkdir(parents=True, exist_ok=True)
    args.out_html.write_text(html, encoding="utf-8")
    print(f"Built {args.out_html} and {daily_json}")


if __name__ == "__main__":
    main()
