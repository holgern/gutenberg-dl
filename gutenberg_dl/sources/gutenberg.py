from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.parse import urlparse

from defusedxml import ElementTree

from ..net import download_file
from ..utils import (
    EpubMetadata,
    ensure_parent_dir,
    make_book_filename,
    resolve_output_path,
)


@dataclass(frozen=True)
class DownloadResult:
    output_path: str
    metadata: EpubMetadata


def download_epub(
    url: str,
    out_path: Optional[str],
    no_images: bool,
    log: Callable[[str], None],
) -> DownloadResult:
    download_url = derive_download_url(url, no_images)
    log(f"Downloading EPUB from {download_url}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp:
        temp_path = tmp.name
    download_file(download_url, temp_path)

    metadata = read_epub_metadata(temp_path)
    default_name = make_book_filename(metadata.author, metadata.title)
    output_path = resolve_output_path(out_path, default_name)
    ensure_parent_dir(output_path)
    shutil.move(temp_path, output_path)

    return DownloadResult(output_path=output_path, metadata=metadata)


def derive_download_url(url: str, no_images: bool) -> str:
    parsed = urlparse(url)
    path = parsed.path
    if (
        path.endswith(".epub")
        or path.endswith(".epub3")
        or path.endswith(".epub3.images")
    ):
        return url

    match = re.search(r"/ebooks/(\d+)", path)
    if not match:
        raise ValueError("Could not determine Project Gutenberg ebook id from URL.")

    book_id = match.group(1)
    base = f"{parsed.scheme or 'https'}://{parsed.netloc or 'www.gutenberg.org'}/ebooks/{book_id}"
    suffix = ".epub3" if no_images else ".epub3.images"
    return f"{base}{suffix}"


def read_epub_metadata(path: str) -> EpubMetadata:
    with zipfile.ZipFile(path, "r") as zip_handle:
        container = zip_handle.read("META-INF/container.xml")
        container_root = ElementTree.fromstring(container)
        rootfile = container_root.find(".//{*}rootfile")
        if rootfile is None:
            return EpubMetadata(title=None, author=None, language=None)
        opf_path = rootfile.get("full-path")
        if not opf_path:
            return EpubMetadata(title=None, author=None, language=None)
        opf_data = zip_handle.read(opf_path)

    opf_root = ElementTree.fromstring(opf_data)
    metadata = opf_root.find(".//{*}metadata")
    if metadata is None:
        return EpubMetadata(title=None, author=None, language=None)

    title = _find_text(metadata, "title")
    author = _find_text(metadata, "creator")
    language = _find_text(metadata, "language")
    return EpubMetadata(title=title, author=author, language=language)


def _find_text(root: ElementTree.Element, local_name: str) -> Optional[str]:
    for node in root.iter():
        if node.tag.endswith(f"}}{local_name}") or node.tag == local_name:
            if node.text:
                text = node.text.strip()
                if text:
                    return text
    return None
