from pathlib import Path

import pytest
from pypdf import PdfWriter

from tools.doc_loader import DocumentLoader


@pytest.fixture
def loader():
    return DocumentLoader()


def test_load_txt_file(loader, tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Hello, AI Agent Builder!", encoding="utf-8")

    result = loader.load(file_path)

    assert result == "Hello, AI Agent Builder!"


def test_load_txt_with_utf8_bom(loader, tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "\ufeffHello from UTF-8!",
        encoding="utf-8",
    )

    result = loader.load(file_path)

    assert result == "Hello from UTF-8!"


def test_missing_file_raises_error(loader, tmp_path):
    file_path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        loader.load(file_path)


def test_unsupported_file_type(loader, tmp_path):
    file_path = tmp_path / "sample.docx"
    file_path.write_text("Not supported", encoding="utf-8")

    with pytest.raises(ValueError):
        loader.load(file_path)


def test_file_size_limit(tmp_path):
    loader = DocumentLoader(max_file_size=5)
    file_path = tmp_path / "large.txt"
    file_path.write_text("This file is too large.", encoding="utf-8")

    with pytest.raises(ValueError):
        loader.load(file_path)


def test_empty_file_raises_error(loader, tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        loader.load(file_path)


def test_text_length_limit(tmp_path):
    loader = DocumentLoader(max_text_length=5)
    file_path = tmp_path / "long.txt"
    file_path.write_text("This text is too long.", encoding="utf-8")

    with pytest.raises(ValueError):
        loader.load(file_path)


def test_load_pdf_file(loader, tmp_path):
    file_path = tmp_path / "sample.pdf"

    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)

    with file_path.open("wb") as file:
        writer.write(file)

    # Blank PDF has no extractable text.
    with pytest.raises(ValueError, match="No readable text"):
        loader.load(file_path)


def test_invalid_pdf_raises_error(loader, tmp_path):
    file_path = tmp_path / "broken.pdf"
    file_path.write_text("This is not a valid PDF.", encoding="utf-8")

    with pytest.raises(Exception):
        loader.load(file_path)