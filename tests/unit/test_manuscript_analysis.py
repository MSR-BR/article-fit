from __future__ import annotations

import json
import zipfile
from io import BytesIO

import pytest
from fastapi import HTTPException
from journal_matcher_api.manuscript_analysis import (
    annotate_docx,
    build_recommendations,
    create_docx,
    create_pdf,
    extract_official_rules,
    scientific_invariants,
    validate_artifacts,
    validate_invariant_preservation,
    validate_proposal_parity,
)


def test_extracts_provenanced_rules_and_marks_conflicts() -> None:
    snapshots = [
        {
            "source_id": "guide-1",
            "source_type": "official-guide",
            "content_hash": "sha256:a",
            "content": "Abstract must not exceed 250 words. Include a data availability statement.",
        },
        {
            "source_id": "scope-1",
            "source_type": "official-scope",
            "content_hash": "sha256:b",
            "content": "The abstract maximum is 200 words. Competing interests are required.",
        },
    ]
    rules = extract_official_rules(snapshots)
    assert next(rule for rule in rules if rule["key"] == "abstract-word-limit")["status"] == "conflict"
    data_rule = next(rule for rule in rules if rule["key"] == "data-availability")
    assert data_rule["sourceId"] == "guide-1"
    assert str(data_rule["locator"]).startswith("characters:")


def test_recommendation_authority_and_scientific_invariants() -> None:
    manuscript = "Abstract\n" + "result 12 mg " * 80 + "\nMethods\nMethod text [1].\nResults\nx = 2"
    profile = {
        "id": "profile",
        "claims": [{"key": "section:discussion", "coverage": "5 of 6 articles", "sourceIds": ["article-1"]}],
    }
    rules = [
        {
            "id": "rule",
            "key": "abstract-word-limit",
            "value": 100,
            "sourceId": "guide",
            "locator": "characters:1-20",
            "status": "validated",
        }
    ]
    recommendations = build_recommendations(manuscript, profile, rules, "paragraph:1")
    official = next(item for item in recommendations if item["key"] == "abstract-word-limit")
    observed = next(item for item in recommendations if item["key"] == "observed-section:discussion")
    assert official["severity"] == "required"
    assert official["scientificImpact"] is True
    assert observed["severity"] == "strongly-recommended"
    invariants = scientific_invariants(manuscript)
    assert "12" in invariants["numbers"]
    assert "12 mg" in invariants["units"]
    assert "[1]" in invariants["citations"]


def test_artifact_bundle_is_structurally_valid_and_private() -> None:
    recommendations = [
        {
            "category": "language",
            "anchor": "paragraph:1",
            "decision": "modified",
            "modifiedText": "Clearer sentence.",
        }
    ]
    docx = create_docx("Title\nOriginal manuscript.", recommendations, reconstructed=False)
    with zipfile.ZipFile(BytesIO(docx)) as archive:
        xml = archive.read("word/document.xml").decode()
    assert "Clearer sentence" in xml
    assert "1F4E79" in xml
    revised_pdf = create_pdf("Revised", ["Original manuscript."])
    report_pdf = create_pdf("Report", ["No acceptance guarantee."])
    manifest = json.dumps({"schemaVersion": "1.0"}).encode()
    assert validate_artifacts(docx, revised_pdf, report_pdf, manifest) == {
        "structural": True,
        "privacy": True,
        "manifestSchema": True,
    }
    with pytest.raises(HTTPException, match="privacy"):
        validate_artifacts(docx, revised_pdf, report_pdf, b'{"schemaVersion":"1.0","token":"Bearer secret"}')


def test_annotation_preserves_original_docx_and_scientific_invariants() -> None:
    original = create_docx("Study title\nResult was 12 mg [1].", [], reconstructed=False)
    annotated = annotate_docx(
        original,
        [{"category": "structure", "anchor": "paragraph:2", "decision": "modified", "modifiedText": "Note."}],
    )
    with zipfile.ZipFile(BytesIO(annotated)) as archive:
        xml = archive.read("word/document.xml").decode()
    assert "Result was 12 mg [1]." in xml
    assert "Note." in xml
    validate_invariant_preservation("Result was 12 mg [1].", "Result was 12 mg [1].\nNote.")
    with pytest.raises(HTTPException, match="invariant"):
        validate_invariant_preservation("Result was 12 mg [1].", "Result was revised.")


def test_artifact_proposal_parity() -> None:
    recommendation = {
        "category": "language",
        "anchor": "paragraph:2",
        "decision": "modified",
        "modifiedText": "Author-approved note.",
    }
    docx = create_docx("Title\nBody", [recommendation], reconstructed=False)
    pdf = create_pdf("Revision", ["Author-approved note."])
    validate_proposal_parity(docx, pdf, [recommendation])
    with pytest.raises(HTTPException, match="parity"):
        validate_proposal_parity(docx, create_pdf("Revision", ["Missing note"]), [recommendation])


def test_annotation_preserves_complex_parts_and_scrubs_personal_metadata() -> None:
    original = create_docx("Title\nBody", [], reconstructed=False)
    source = BytesIO()
    with zipfile.ZipFile(BytesIO(original)) as archive, zipfile.ZipFile(source, "w") as enriched:
        for name in archive.namelist():
            enriched.writestr(name, archive.read(name))
        enriched.writestr("word/media/figure.png", b"synthetic-image")
        enriched.writestr("word/footnotes.xml", b"<w:footnotes xmlns:w='urn:test'/>")
        enriched.writestr(
            "docProps/core.xml",
            b"<cp:coreProperties xmlns:cp='urn:cp' xmlns:dc='urn:dc'>"
            b"<dc:creator>Private Author</dc:creator>"
            b"<cp:lastModifiedBy>Private Editor</cp:lastModifiedBy></cp:coreProperties>",
        )
        enriched.writestr("docProps/custom.xml", b"<Properties>private</Properties>")
    annotated = annotate_docx(source.getvalue(), [])
    with zipfile.ZipFile(BytesIO(annotated)) as archive:
        assert archive.read("word/media/figure.png") == b"synthetic-image"
        assert archive.read("word/footnotes.xml").startswith(b"<w:footnotes")
        assert b"Private Author" not in archive.read("docProps/core.xml")
        assert "docProps/custom.xml" not in archive.namelist()
