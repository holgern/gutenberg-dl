# gutenberg-dl

CLI tool to download or build EPUB files from Projekt Gutenberg and Project Gutenberg
sources.

## Usage

```bash
gutenberg-dl "https://projekt-gutenberg.org/authors/thomas-mann/books/achtzehn-erzaehlungen/"
gutenberg-dl "https://www.gutenberg.org/ebooks/77830"
gutenberg-dl --no-images "https://www.gutenberg.org/ebooks/77830"
gutenberg-dl --debug "https://projekt-gutenberg.org/authors/thomas-mann/books/achtzehn-erzaehlungen/"
```

## Options

- `--no-images`: Skip image downloads. For Project Gutenberg URLs this switches to
  `.epub3` without images.
- `--debug`: Save debug HTML output for Projekt Gutenberg sources. Writes raw chapter
  HTML and extracted content under `./gutenberg-dl-debug/<slug>/` (or under `--out` if
  it is a directory).

## Hinweis zu den Inhalten (Projekt Gutenberg)

Die auf dieser Website veröffentlichten literarischen Werke sind nach bestem Wissen und
Gewissen als gemeinfrei eingestuft und werden mit größtmöglicher Sorgfalt
bereitgestellt. Dennoch wird keine Gewähr dafür übernommen, dass alle Texte vollständig
frei von Urheberrechten sind. Etwaige Ansprüche von Rechteinhabern bleiben ausdrücklich
gewahrt.

Die auf dieser Website bereitgestellten Texte dürfen ausschließlich zum privaten
Gebrauch gelesen und genutzt werden. Eine Vervielfältigung, Weitergabe, Veröffentlichung
oder sonstige Nutzung über den privaten Gebrauch hinaus ist nicht gestattet. Für eine
Nutzung in anderen Zusammenhängen ist vorab eine eigenständige rechtliche Prüfung
erforderlich.
