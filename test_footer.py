import io
import subprocess
import sys

import pikepdf
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas

from footer import add_footer

LETTER_MARKER = "Letter body text marker"
A4_MARKER = "A4 body text marker"


def make_source_pdf(path):
    """Build a 3-page PDF with mixed page sizes and known body text."""
    writer = PdfWriter()

    for size, marker in [(LETTER, LETTER_MARKER), (A4, A4_MARKER), (LETTER, LETTER_MARKER)]:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=size)
        c.setFont("Helvetica", 12)
        c.drawString(72, size[1] - 72, marker)
        c.save()
        buffer.seek(0)
        reader = PdfReader(buffer)
        writer.add_page(reader.pages[0])

    with open(path, "wb") as f:
        writer.write(f)


def test_footer_adds_identifier_and_page_numbers(tmp_path):
    src = tmp_path / "source.pdf"
    out = tmp_path / "output.pdf"
    make_source_pdf(src)

    add_footer(str(src), str(out), "Combined Report 2026")

    reader = PdfReader(str(out))
    assert len(reader.pages) == 3

    expected_markers = [LETTER_MARKER, A4_MARKER, LETTER_MARKER]
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        assert "Combined Report 2026" in text
        assert f"Page {i}/3" in text
        assert expected_markers[i - 1] in text


def test_footer_preserves_page_sizes(tmp_path):
    src = tmp_path / "source.pdf"
    out = tmp_path / "output.pdf"
    make_source_pdf(src)

    add_footer(str(src), str(out), "ID")

    src_reader = PdfReader(str(src))
    out_reader = PdfReader(str(out))
    for src_page, out_page in zip(src_reader.pages, out_reader.pages):
        assert float(src_page.mediabox.width) == float(out_page.mediabox.width)
        assert float(src_page.mediabox.height) == float(out_page.mediabox.height)


def build_pdf_with_bad_xref_offsets():
    """Build a single-page PDF whose xref table offsets are all wrong, mirroring
    the "Ignoring wrong pointing object" corruption seen in real combined PDFs."""
    objects = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
    )
    objects.append(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    stream_content = b"BT /F1 12 Tf 72 700 Td (Body text page 1) Tj ET"
    objects.append(
        b"5 0 obj\n<< /Length %d >>\nstream\n%s\nendstream\nendobj\n" % (len(stream_content), stream_content)
    )

    body = b"%PDF-1.4\n"
    offsets = []
    for obj in objects:
        offsets.append(len(body))
        body += obj

    xref_start = len(body)
    n = len(objects) + 1
    xref = b"xref\n0 %d\n" % n
    xref += b"0000000000 65535 f \n"
    for off in offsets:
        bad_off = off + 5  # deliberately wrong: doesn't point at "N 0 obj"
        xref += b"%010d 00000 n \n" % bad_off

    trailer = b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (n, xref_start)
    return body + xref + trailer


def test_footer_repairs_malformed_xref(tmp_path):
    """Real-world combined PDFs sometimes have corrupted cross-reference tables.
    add_footer should still succeed and produce correct, complete output."""
    src = tmp_path / "corrupt.pdf"
    out = tmp_path / "output.pdf"
    src.write_bytes(build_pdf_with_bad_xref_offsets())

    add_footer(str(src), str(out), "Repaired ID")

    reader = PdfReader(str(out))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "Body text page 1" in text
    assert "Repaired ID" in text
    assert "Page 1/1" in text


def test_footer_preserves_form_widget_annotations(tmp_path):
    src = tmp_path / "form.pdf"
    out = tmp_path / "output.pdf"

    c = canvas.Canvas(str(src), pagesize=LETTER)
    c.drawString(72, 700, "Form page")
    c.acroForm.checkbox(name="cb1", x=100, y=650, buttonStyle="check", tooltip="Test checkbox")
    c.save()

    add_footer(str(src), str(out), "ID")

    with pikepdf.open(str(out)) as pdf:
        annots = pdf.pages[0].get("/Annots", [])
        assert len(annots) == 1
        assert annots[0].get("/Subtype") == pikepdf.Name("/Widget")


def test_footer_single_page(tmp_path):
    src = tmp_path / "source.pdf"
    out = tmp_path / "output.pdf"

    c = canvas.Canvas(str(src), pagesize=LETTER)
    c.drawString(72, 700, "Only page")
    c.save()

    add_footer(str(src), str(out), "Solo ID")

    reader = PdfReader(str(out))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "Solo ID" in text
    assert "Page 1/1" in text


def test_cli_smoke(tmp_path):
    src = tmp_path / "source.pdf"
    out = tmp_path / "output.pdf"
    make_source_pdf(src)

    result = subprocess.run(
        [sys.executable, "footer.py", str(src), str(out), "CLI Identifier"],
        cwd=__file__.rsplit("/", 1)[0],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()

    reader = PdfReader(str(out))
    assert len(reader.pages) == 3
    assert "CLI Identifier" in reader.pages[0].extract_text()
