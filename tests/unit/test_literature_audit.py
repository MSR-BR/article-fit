from __future__ import annotations

from journal_matcher_api.literature_audit import (
    extract_bibliography,
    extract_manuscript_literature_context,
    manuscript_reference_evidence,
    recent_literature_evidence,
    source_catalog,
)


def test_extracts_numbered_bibliography_and_identifiers() -> None:
    text = """A compact quantum thermodynamics result

Abstract
We derive and validate a perturbative thermodynamic relation.

Introduction
Main text.

References
[1] A. Author, First result, Phys. Rev. Lett. 120, 1 (2021), doi:10.1103/PhysRevLett.120.000001.
[2] B. Author, Open preprint, arXiv:2407.08344v4 (2024).
3. C. Author, Earlier context, Journal 5, 10 (2018).
"""

    context = extract_manuscript_literature_context(text)

    assert context.title == "A compact quantum thermodynamics result"
    assert "perturbative thermodynamic relation" in context.abstract
    assert len(context.bibliography) == 3
    assert context.bibliography[0].doi == "10.1103/physrevlett.120.000001"
    assert context.bibliography[1].arxiv_id == "2407.08344"
    assert context.bibliography[2].year == 2018
    assert "small number" in context.limitations[0]

    evidence = manuscript_reference_evidence(context)
    assert evidence[0]["sourceType"] == "manuscript-reference"
    assert evidence[0]["identifier"] == "10.1103/physrevlett.120.000001"
    assert evidence[1]["identifier"] == "arXiv:2407.08344"
    assert len({item["sourceId"] for item in evidence}) == 3


def test_handles_unnumbered_and_missing_bibliographies() -> None:
    unnumbered = """Submitted manuscript
Abstract
Short abstract.
Bibliography
Author One, A sufficiently long unnumbered bibliography entry, Journal 1 (2020).
Author Two, Another sufficiently long unnumbered bibliography entry, Journal 2 (2022).
"""
    context = extract_manuscript_literature_context(unnumbered)
    assert len(context.bibliography) == 2
    assert "small number" in context.limitations[0]

    missing = extract_manuscript_literature_context("Manuscript title\nA paragraph without a delimited bibliography.")
    assert missing.bibliography == ()
    assert "No reliably delimited bibliography" in missing.limitations[0]
    assert extract_bibliography("No reference section here") == ()


def test_detects_dense_end_bibliography_without_heading() -> None:
    text = (
        "Long manuscript body with equations and discussion. " * 40
        + "\n[1] First complete reference, Physical Review Letters 120, 1 (2020)."
        + "\n[2] Second complete reference, Physical Review E 10, 2 (2021)."
        + "\n[3] Third complete reference, Nature Physics 3, 3 (2022)."
        + "\n[4] Fourth complete reference, PRX Quantum 4, 4 (2023)."
        + "\n[5] Fifth complete reference, Science 5, 5 (2024)."
        + "\n[6] Sixth complete reference, arXiv:2501.01234 (2025)."
    )

    bibliography = extract_bibliography(text)

    assert len(bibliography) == 6
    assert bibliography[0].number == 1
    assert bibliography[-1].arxiv_id == "2501.01234"


def test_builds_deduplicated_recent_evidence_and_catalog() -> None:
    papers = [
        {"title": "Recent result", "doi": "10.1000/example", "year": 2025},
        {"paperTitle": "Preprint result", "arxivId": "2501.01234", "publishedYear": 2025},
    ]
    references = [
        {"citation": "Recent result", "doi": "10.1000/example", "publicationYear": 2025},
        {"name": "Context paper", "url": "https://example.org/paper", "year": 2023},
        {"id": 42},
    ]

    evidence = recent_literature_evidence(references, papers)

    assert len(evidence) == 4
    assert evidence[0]["label"] == "Recent result"
    assert evidence[1]["identifier"] == "2501.01234"
    assert evidence[-1]["label"] == "Literature candidate"
    assert all(item["status"] == "recent-literature-candidate" for item in evidence)

    catalog = source_catalog(evidence)
    assert set(catalog) == {item["sourceId"] for item in evidence}
    assert "10.1000/example" in catalog[evidence[0]["sourceId"]]
