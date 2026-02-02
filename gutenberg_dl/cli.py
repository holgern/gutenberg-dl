from __future__ import annotations

import os
from urllib.parse import urlparse

import click

from .epub import build_epub
from .sources import download_epub, fetch_book
from .utils import make_book_filename, resolve_output_path, slugify


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme:
        return url
    return f"https://{url.lstrip('/')}"


def _detect_source(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "projekt-gutenberg.org" in host:
        return "projekt"
    if "gutenberg.org" in host:
        return "gutenberg"
    raise click.ClickException(
        "Unsupported URL. Use projekt-gutenberg.org or gutenberg.org URLs."
    )


def _logger(quiet: bool):
    def log(message: str) -> None:
        if not quiet:
            click.echo(message, err=True)

    return log


@click.command()
@click.argument("url")
@click.option("--out", "out_path", type=click.Path(path_type=str), default=None)
@click.option(
    "--source",
    type=click.Choice(["auto", "projekt", "gutenberg"], case_sensitive=False),
    default="auto",
    show_default=True,
)
@click.option(
    "--no-images", is_flag=True, default=False, help="Skip downloading images."
)
@click.option("--quiet", is_flag=True, default=False, help="Suppress progress output.")
@click.option("--debug", is_flag=True, default=False, help="Save debug HTML output.")
def main(
    url: str,
    out_path: str | None,
    source: str,
    no_images: bool,
    quiet: bool,
    debug: bool,
) -> None:
    """Download or build EPUB files from Gutenberg sources."""
    url = _normalize_url(url)
    log = _logger(quiet)

    if source == "auto":
        source = _detect_source(url)
    else:
        source = source.lower()

    if source == "gutenberg":
        result = download_epub(url, out_path, no_images, log)
        log(f"Saved EPUB to {result.output_path}")
        return

    debug_dir = None
    if debug:
        base_dir = os.getcwd()
        if out_path and os.path.isdir(out_path):
            base_dir = out_path
        elif out_path:
            base_dir = os.path.dirname(out_path) or base_dir
        debug_dir = os.path.join(base_dir, "gutenberg-dl-debug", slugify(url))
        log(f"Writing debug files to {debug_dir}")

    book = fetch_book(url, no_images, log, debug_dir=debug_dir)
    default_name = make_book_filename(book.author, book.title)
    output_path = resolve_output_path(out_path, default_name)
    build_epub(book, output_path)
    log(f"Saved EPUB to {output_path}")
