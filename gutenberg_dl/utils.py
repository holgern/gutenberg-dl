from __future__ import annotations

import mimetypes
import os
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass(frozen=True)
class EpubMetadata:
    title: Optional[str]
    author: Optional[str]
    language: Optional[str]


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.lower()
    ascii_value = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return ascii_value or "book"


def make_book_filename(author: Optional[str], title: Optional[str]) -> str:
    parts = [part for part in [author, title] if part]
    if not parts:
        return "gutenberg-book.epub"
    base = "-".join(parts)
    return f"{slugify(base)}.epub"


def resolve_output_path(out_path: Optional[str], default_name: str) -> str:
    if not out_path:
        return default_name
    if out_path.endswith(os.sep):
        return os.path.join(out_path, default_name)
    if os.path.isdir(out_path):
        return os.path.join(out_path, default_name)
    return out_path


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def unique_filename(filename: str, used: set[str]) -> str:
    if filename not in used:
        used.add(filename)
        return filename
    base, ext = os.path.splitext(filename)
    index = 1
    while True:
        candidate = f"{base}-{index}{ext}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        index += 1


def guess_extension(url: str, media_type: Optional[str]) -> str:
    if media_type:
        guessed = mimetypes.guess_extension(media_type.split(";")[0].strip())
        if guessed:
            return guessed
    parsed = urlparse(url)
    _, ext = os.path.splitext(parsed.path)
    return ext or ".bin"


def clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def first_text(values: Iterable[Optional[str]]) -> Optional[str]:
    for value in values:
        if value:
            return value
    return None
