from __future__ import annotations

import zipfile
from io import BytesIO

import pytest
from fastapi import HTTPException
from journal_matcher_api.foundation import MAX_FILE_BYTES, validate_and_extract

from tests.conftest import synthetic_docx, synthetic_pdf


def test_pdf_and_docx_produce_stable_anchors() -> None:
    pdf = validate_and_extract("reference-1", "paper.pdf", "application/pdf", synthetic_pdf())
    docx = validate_and_extract(
        "manuscript",
        "draft.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        synthetic_docx(),
    )
    assert pdf["segments"][0]["anchor"] == "page:1"  # type: ignore[index]
    assert docx["segments"][0]["anchor"] == "paragraph:1"  # type: ignore[index]
    assert float(pdf["quality"]) > 0.9
    assert "methods results discussion" in pdf["segments"][0]["text"]  # type: ignore[index]


def test_pdf_container_bytes_are_not_mistaken_for_article_text() -> None:
    malformed = b"%PDF-1.7\n1 0 obj <</Type /Page>>\n" + b"xref endobj stream compressed " * 30 + b"\n%%EOF"
    with pytest.raises(HTTPException, match="invalid or unreadable"):
        validate_and_extract("reference-1", "broken.pdf", "application/pdf", malformed)


@pytest.mark.parametrize(
    ("content", "media_type", "expected_status"),
    [
        (b"not a document", "application/pdf", 415),
        (b"%PDF-1.7 EICAR-STANDARD-ANTIVIRUS-TEST-FILE", "application/pdf", 422),
        (b"%PDF-1.7 short", "application/pdf", 422),
        (synthetic_pdf(), "application/msword", 415),
    ],
)
def test_invalid_files_fail_closed(content: bytes, media_type: str, expected_status: int) -> None:
    with pytest.raises(HTTPException) as error:
        validate_and_extract("reference-1", "paper.pdf", media_type, content)
    assert error.value.status_code == expected_status


def test_oversized_file_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        validate_and_extract("reference-1", "paper.pdf", "application/pdf", b"%PDF-" + b"a" * MAX_FILE_BYTES)
    assert error.value.status_code == 413


def test_rejects_unsafe_docx_archive_paths() -> None:
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("word/document.xml", "<document>safe text content</document>")
        archive.writestr("../escape.txt", "unsafe")
    with pytest.raises(HTTPException, match="valid PDF or DOCX"):
        validate_and_extract(
            "manuscript",
            "unsafe.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            stream.getvalue(),
        )
