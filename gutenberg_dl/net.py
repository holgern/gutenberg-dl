from __future__ import annotations

import ssl
from dataclasses import dataclass
from typing import Optional
from urllib.request import Request, urlopen

DEFAULT_USER_AGENT = "gutenberg-dl/0.1 (+https://github.com/holgern/gutenberg-dl)"


@dataclass(frozen=True)
class FetchResult:
    content: bytes
    final_url: str
    content_type: Optional[str]


def fetch_bytes(url: str, timeout: int = 30) -> FetchResult:
    request = Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    context = ssl.create_default_context()
    with urlopen(request, timeout=timeout, context=context) as response:
        content = response.read()
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type")
    return FetchResult(content=content, final_url=final_url, content_type=content_type)


def fetch_text(url: str, timeout: int = 30) -> FetchResult:
    return fetch_bytes(url, timeout=timeout)


def download_file(url: str, dest_path: str, timeout: int = 60) -> FetchResult:
    result = fetch_bytes(url, timeout=timeout)
    with open(dest_path, "wb") as handle:
        handle.write(result.content)
    return result
