# FootStamp

FootStamp adds a footer to each page of a PDF file. The footer shows a text
identifier on the left and a page number on the right (`Page N/M`).

Use FootStamp on a PDF that combines documents from many sources. FootStamp
does not change any other content in the file.

## Requirements

- Python 3.9 or later

## Setup

Run these commands in the project folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

```bash
.venv/bin/python footer.py <input.pdf> <output.pdf> "<identifier text>"
```

- `<input.pdf>` is the PDF file to stamp.
- `<output.pdf>` is the path for the new, stamped file.
- `<identifier text>` is the text to show on the left of the footer.

FootStamp counts the pages in the input file. You do not need to supply the
total page count.

The input file is not changed. FootStamp writes a new file at the output
path.

## Testing

Run the test suite with this command:

```bash
.venv/bin/pytest -q
```
