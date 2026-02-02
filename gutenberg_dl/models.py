from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chapter:
    title: str
    html: str
    file_name: str


@dataclass(frozen=True)
class ImageAsset:
    url: str
    file_name: str
    media_type: str
    content: bytes


@dataclass(frozen=True)
class Book:
    title: str
    author: str
    language: str
    identifier: str
    description: str | None
    source_url: str
    chapters: list[Chapter]
    images: list[ImageAsset]
