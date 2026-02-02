from __future__ import annotations

import html

from ebooklib import epub

from .models import Book, Chapter
from .utils import ensure_parent_dir

DEFAULT_CSS = """
body {
  font-family: serif;
  line-height: 1.6;
  margin: 1.2em;
}
h1, h2 {
  text-align: center;
}
.center {
  text-align: center;
}
.centersml {
  text-align: center;
  font-size: 0.9em;
}
.title {
  text-align: center;
  font-size: 1.4em;
  margin-bottom: 0.8em;
}
img {
  max-width: 100%;
  height: auto;
}
"""


def wrap_chapter_html(title: str, body_html: str, language: str) -> str:
    safe_title = html.escape(title, quote=True)
    if not body_html.strip():
        body_html = "<p></p>"
    return (
        "<!DOCTYPE html>\n"
        f'<html xmlns="http://www.w3.org/1999/xhtml" lang="{language}">\n'
        "<head>\n"
        f"  <title>{safe_title}</title>\n"
        '  <meta charset="utf-8" />\n'
        "</head>\n"
        "<body>\n"
        f"  <h2>{safe_title}</h2>\n"
        f"{body_html}\n"
        "</body>\n"
        "</html>\n"
    )


def _add_chapters(
    epub_book: epub.EpubBook,
    chapters: list[Chapter],
    language: str,
    style_item: epub.EpubItem,
) -> list[epub.EpubHtml]:
    items: list[epub.EpubHtml] = []
    for chapter in chapters:
        item = epub.EpubHtml(
            title=chapter.title, file_name=chapter.file_name, lang=language
        )
        item.content = chapter.html
        item.add_item(style_item)
        epub_book.add_item(item)
        items.append(item)
    return items


def build_epub(book: Book, output_path: str) -> str:
    epub_book = epub.EpubBook()
    epub_book.set_identifier(book.identifier)
    epub_book.set_title(book.title)
    epub_book.set_language(book.language)
    if book.author:
        epub_book.add_author(book.author)
    if book.description:
        epub_book.add_metadata("DC", "description", book.description)
    if book.source_url:
        epub_book.add_metadata("DC", "source", book.source_url)

    style_item = epub.EpubItem(
        uid="style",
        file_name="style/style.css",
        media_type="text/css",
        content=DEFAULT_CSS,
    )
    epub_book.add_item(style_item)

    for image in book.images:
        img_item = epub.EpubImage()
        img_item.file_name = image.file_name
        img_item.media_type = image.media_type
        img_item.content = image.content
        epub_book.add_item(img_item)

    chapter_items = _add_chapters(epub_book, book.chapters, book.language, style_item)
    epub_book.toc = [
        epub.Link(item.file_name, item.title, item.file_name) for item in chapter_items
    ]
    epub_book.spine = ["nav"] + chapter_items
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())

    ensure_parent_dir(output_path)
    epub.write_epub(output_path, epub_book)
    return output_path
