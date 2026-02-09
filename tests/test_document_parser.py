import pytest
from app.services.document_parser import extract_text


def test_extract_text_plain():
    text = extract_text(b"Hello world resume", "text/plain")
    assert "Hello world" in text


def test_extract_text_unsupported():
    with pytest.raises(ValueError, match="Unsupported content type"):
        extract_text(b"data", "application/zip")


def test_extract_text_utf8_errors():
    text = extract_text(b"\xff\xfe Hello", "text/plain")
    assert "Hello" in text
