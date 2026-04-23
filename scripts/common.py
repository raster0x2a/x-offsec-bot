from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

UTC = timezone.utc
JST = timezone(timedelta(hours=9))


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    clean_query = urlencode(query)
    normalized = parsed._replace(query=clean_query, fragment="")
    return urlunparse(normalized)


def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    pattern = r"https?://[^\s]+"
    return re.findall(pattern, text)


@dataclass
class Post:
    post_id: str
    text: str
    author: str
    created_at: str
    post_url: str
    external_urls: list[str]
    source: str = "x"

    def to_dict(self) -> dict[str, Any]:
        return {
            "post_id": self.post_id,
            "text": self.text,
            "author": self.author,
            "created_at": self.created_at,
            "post_url": self.post_url,
            "external_urls": self.external_urls,
            "source": self.source,
        }
