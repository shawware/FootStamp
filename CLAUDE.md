# Footer

A script that stamps a footer onto every page of a combined PDF: a text identifier
on the left, "Page N/M" on the right. See `Brief.txt` for the original requirements.

## Layout

- `footer.py` — the script. Entry point is `main()`; core logic is `add_footer()`.
- `test_footer.py` — pytest tests.
- `requirements.txt` — `pikepdf`, `pypdf`, `reportlab`, `pytest`.
- `.venv/` — local virtualenv (not committed).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python footer.py <input.pdf> <output.pdf> "<identifier text>"
```

Total page count is derived from the input PDF; it is not a CLI argument.

## Test

```bash
.venv/bin/pytest -q
```

## Design notes

- Overlay-based approach: `reportlab` draws a per-page footer overlay sized to
  match each page's own mediabox, `pikepdf` merges it onto the page via
  `Page.add_overlay()`. This keeps footers correctly positioned even when
  source pages have mixed sizes (e.g. Letter + A4), which is expected since
  the input PDF is combined from many external sources.
- Read/write engine is `pikepdf` (built on `qpdf`), not `pypdf`. Real-world
  combined PDFs from unknown sources often have malformed cross-reference
  tables; `pypdf`'s lenient parser patches around this by duplicating objects
  and losing the original stream compression, which both spams warnings and
  can nearly double output file size. `pikepdf`/`qpdf` repairs the xref table
  on open and writes with proper stream/object-stream compression
  (`compress_streams=True`, `object_stream_mode=pikepdf.ObjectStreamMode.generate`),
  avoiding both problems. `pypdf` is kept only as a test-side reader (building
  synthetic fixtures, extracting text to assert on).
- No other content, metadata, or structure is modified — only the footer is
  added.
- Add tests for any new or changed functionality (see `test_footer.py` for the
  pattern: build a synthetic source PDF in a temp dir, run the function, assert
  on extracted text and page geometry).
