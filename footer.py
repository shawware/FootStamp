#!/usr/bin/env python3
"""Stamp a left-aligned identifier and right-aligned page number footer onto every page of a PDF."""

import argparse
import io
import sys

import pikepdf
from reportlab.pdfgen import canvas

MARGIN_BOTTOM = 36  # 0.5 inch
MARGIN_SIDE = 36  # 0.5 inch
FONT_NAME = "Helvetica-Oblique"
FONT_SIZE = 9


def make_footer_overlay(width: float, height: float, identifier: str, page_number: int, total_pages: int) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_SIDE, MARGIN_BOTTOM, identifier)
    page_label = f"Page {page_number}/{total_pages}"
    c.drawRightString(width - MARGIN_SIDE, MARGIN_BOTTOM, page_label)
    c.save()
    buffer.seek(0)
    return buffer.read()


def add_footer(input_path: str, output_path: str, identifier: str) -> None:
    with pikepdf.open(input_path) as pdf:
        total_pages = len(pdf.pages)

        for page_number, page in enumerate(pdf.pages, start=1):
            mediabox = page.mediabox
            width = float(mediabox[2] - mediabox[0])
            height = float(mediabox[3] - mediabox[1])

            overlay_bytes = make_footer_overlay(width, height, identifier, page_number, total_pages)
            with pikepdf.open(io.BytesIO(overlay_bytes)) as overlay_pdf:
                page.add_overlay(overlay_pdf.pages[0])

        pdf.save(
            output_path,
            compress_streams=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_pdf", help="Path to the combined input PDF")
    parser.add_argument("output_pdf", help="Path to write the footer-stamped PDF")
    parser.add_argument("identifier", help="Text identifier to show on the left of the footer")
    args = parser.parse_args(argv)

    add_footer(args.input_pdf, args.output_pdf, args.identifier)
    return 0


if __name__ == "__main__":
    sys.exit(main())
