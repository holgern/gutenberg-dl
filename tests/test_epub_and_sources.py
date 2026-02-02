import tempfile

from gutenberg_dl.epub import build_epub, wrap_chapter_html
from gutenberg_dl.models import Book, Chapter
from gutenberg_dl.sources.gutenberg import derive_download_url


def test_derive_download_url_with_images() -> None:
    url = "https://www.gutenberg.org/ebooks/77830"
    assert (
        derive_download_url(url, no_images=False)
        == "https://www.gutenberg.org/ebooks/77830.epub3.images"
    )


def test_derive_download_url_no_images() -> None:
    url = "https://www.gutenberg.org/ebooks/77830"
    assert (
        derive_download_url(url, no_images=True)
        == "https://www.gutenberg.org/ebooks/77830.epub3"
    )


def test_wrap_chapter_html_non_empty() -> None:
    html = wrap_chapter_html("Titel", "", "de")
    assert "<h2>Titel</h2>" in html
    assert "<p></p>" in html


def test_build_epub_with_empty_chapter() -> None:
    chapter_html = wrap_chapter_html("Kapitel 1", "", "de")
    book = Book(
        title="Testbuch",
        author="Tester",
        language="de",
        identifier="test-id",
        description=None,
        source_url="https://projekt-gutenberg.org/",
        chapters=[
            Chapter(title="Kapitel 1", html=chapter_html, file_name="chap_001.xhtml")
        ],
        images=[],
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = f"{temp_dir}/test.epub"
        result = build_epub(book, output_path)
        assert result == output_path
