from __future__ import annotations

import hashlib
import mimetypes
import os
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from ..epub import wrap_chapter_html
from ..models import Book, Chapter, ImageAsset
from ..net import fetch_bytes
from ..utils import clean_text, guess_extension, slugify, unique_filename


@dataclass(frozen=True)
class ChapterRef:
    url: str
    title: Optional[str]


def fetch_book(
    url: str,
    no_images: bool,
    log: Callable[[str], None],
    debug_dir: Optional[str] = None,
) -> Book:
    page = fetch_bytes(url)
    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)
        _write_debug_file(debug_dir, "book.html", page.content)
    soup = BeautifulSoup(page.content, "html.parser")

    title = (
        clean_text(_get_text(soup.select_one(".book-reader__title"))) or "Unknown title"
    )
    author = (
        clean_text(_get_text(soup.select_one(".book-reader__author-link")))
        or "Unknown author"
    )
    description = clean_text(_get_text(soup.select_one(".book-reader__description")))
    language = _attr_str(soup.html, "lang") if soup.html else None
    if not language:
        language = "de"

    book_reader = soup.select_one(".book-reader")
    identifier = None
    if book_reader:
        identifier = _attr_str(book_reader, "data-gutenberg-book-id")
    if not identifier:
        identifier = f"projekt-gutenberg:{hashlib.sha1(page.final_url.encode('utf-8')).hexdigest()}"

    chapter_refs = _parse_chapter_refs(soup, page.final_url)
    if not chapter_refs:
        raise ValueError("No chapters found on Projekt Gutenberg page.")

    images: Dict[str, ImageAsset] = {}
    used_names: set[str] = set()
    chapters: List[Chapter] = []

    for index, ref in enumerate(chapter_refs, start=1):
        log(f"Downloading chapter {index}/{len(chapter_refs)}")
        chapter_page = fetch_bytes(ref.url)
        if debug_dir:
            _write_debug_file(
                debug_dir,
                f"chapter-{index:03d}.raw.html",
                chapter_page.content,
            )
        chapter_title, body_html = _parse_chapter_content(
            chapter_page.content,
            chapter_page.final_url,
            no_images,
            images,
            used_names,
        )
        if not chapter_title:
            chapter_title = ref.title or f"Chapter {index}"
        if not body_html.strip():
            body_html = "<p></p>"
        chapter_html = wrap_chapter_html(chapter_title, body_html, language)
        if debug_dir:
            _write_debug_text(
                debug_dir,
                f"chapter-{index:03d}.content.html",
                body_html,
            )
            _write_debug_text(
                debug_dir,
                f"chapter-{index:03d}.xhtml",
                chapter_html,
            )
        chapters.append(
            Chapter(
                title=chapter_title,
                html=chapter_html,
                file_name=f"chap_{index:03d}.xhtml",
            )
        )

    return Book(
        title=title,
        author=author,
        language=language,
        identifier=identifier,
        description=description,
        source_url=page.final_url,
        chapters=chapters,
        images=list(images.values()),
    )


def _parse_chapter_refs(soup: BeautifulSoup, base_url: str) -> List[ChapterRef]:
    refs: List[ChapterRef] = []
    for link in soup.select(".book-reader__chapter-list a"):
        href = _attr_str(link, "href")
        if not href:
            continue
        url = urljoin(base_url, href)
        title = clean_text(_get_text(link.select_one(".book-reader__chapter-title")))
        if not title:
            title = clean_text(_get_text(link))
        refs.append(ChapterRef(url=url, title=title))

    if refs:
        return refs

    for option in soup.select("#book-reader__chapter-select option"):
        href = _attr_str(option, "value")
        if not href:
            continue
        url = urljoin(base_url, href)
        title = clean_text(option.get_text())
        refs.append(ChapterRef(url=url, title=title))

    return refs


def _parse_chapter_content(
    html: bytes,
    base_url: str,
    no_images: bool,
    images: Dict[str, ImageAsset],
    used_names: set[str],
) -> tuple[Optional[str], str]:
    soup = BeautifulSoup(html, "html.parser")
    title = clean_text(_get_text(soup.select_one(".book-reader__chapter-heading")))
    content = soup.select_one(".book-reader__chapter-content-wrapper")
    if content is None:
        content = soup.select_one(".book-reader__chapter-text")
    if content is None:
        return title, ""

    for tag in content.find_all(["script", "style"]):
        tag.decompose()

    if no_images:
        for img in content.find_all("img"):
            img.decompose()
    else:
        _rewrite_images(content, base_url, images, used_names)

    body_html = "".join(str(child) for child in content.contents)
    return title, body_html


def _rewrite_images(
    content: Tag,
    base_url: str,
    images: Dict[str, ImageAsset],
    used_names: set[str],
) -> None:
    for img in content.find_all("img"):
        src = _attr_str(img, "src")
        if not src:
            continue
        image_url = urljoin(base_url, src)
        asset = images.get(image_url)
        if asset is None:
            fetched = fetch_bytes(image_url)
            media_type = _media_type_from_response(fetched.content_type, image_url)
            ext = guess_extension(image_url, media_type)
            parsed = urlparse(image_url)
            base_name = os.path.basename(parsed.path) or "image"
            stem, _ = os.path.splitext(base_name)
            safe_stem = slugify(stem)
            filename = unique_filename(f"{safe_stem}{ext}", used_names)
            asset = ImageAsset(
                url=image_url,
                file_name=f"images/{filename}",
                media_type=media_type,
                content=fetched.content,
            )
            images[image_url] = asset
        img["src"] = asset.file_name
        img.attrs.pop("srcset", None)


def _media_type_from_response(content_type: Optional[str], url: str) -> str:
    if content_type:
        return content_type.split(";")[0].strip()
    guessed, _ = mimetypes.guess_type(url)
    return guessed or "application/octet-stream"


def _get_text(node: Optional[Tag]) -> Optional[str]:
    if node is None:
        return None
    return node.get_text()


def _attr_str(node: Optional[Tag], attr: str) -> Optional[str]:
    if node is None:
        return None
    value = node.get(attr)
    if value is None:
        return None
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def _write_debug_file(debug_dir: str, name: str, content: bytes) -> None:
    path = os.path.join(debug_dir, name)
    with open(path, "wb") as handle:
        handle.write(content)


def _write_debug_text(debug_dir: str, name: str, content: str) -> None:
    path = os.path.join(debug_dir, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
