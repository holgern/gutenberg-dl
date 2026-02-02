from gutenberg_dl.sources import projekt as projekt_source


def test_parse_chapter_content_no_images_removes_imgs() -> None:
    html = b"""
    <html>
      <body>
        <div class="book-reader__chapter-content-wrapper">
          <p>Hallo</p>
          <img src="https://example.com/img.png" />
        </div>
      </body>
    </html>
    """
    images: dict[str, projekt_source.ImageAsset] = {}
    title, body_html = projekt_source._parse_chapter_content(
        html,
        "https://example.com/base",
        True,
        images,
        set(),
    )

    assert title is None
    assert "<img" not in body_html
    assert images == {}
