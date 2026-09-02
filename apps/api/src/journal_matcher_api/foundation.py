"""Secure, provider-neutral MVP ingestion foundation."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sqlite3
import uuid
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Literal, cast

from fastapi import HTTPException, status
from pypdf import PdfReader
from pypdf.errors import PdfReadError

DocumentSlot = Literal["manuscript", "reference-1", "reference-2", "reference-3"]
SLOTS: tuple[DocumentSlot, ...] = (
    "manuscript",
    "reference-1",
    "reference-2",
    "reference-3",
)
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 200
MAX_DOCX_ENTRIES = 2_000
MAX_DOCX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
EPHEMERAL_RETENTION_HOURS = 24


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class Principal:
    user_id: str
    workspace_id: str


class FoundationStore:
    """SQLite metadata plus immutable private filesystem objects."""

    def __init__(self, database_path: Path, object_root: Path) -> None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        object_root.mkdir(parents=True, exist_ok=True)
        self.database_path = database_path
        self.object_root = object_root
        self._migrate()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                yield connection
        finally:
            connection.close()

    def _migrate(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    journal_candidate TEXT NOT NULL,
                    journal_title TEXT,
                    journal_issn TEXT,
                    journal_domain TEXT,
                    journal_confirmed_at TEXT,
                    created_at TEXT NOT NULL,
                    deleted_at TEXT
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id),
                    workspace_id TEXT NOT NULL,
                    slot TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    byte_size INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    object_key TEXT NOT NULL,
                    malware_status TEXT NOT NULL,
                    extraction_quality REAL NOT NULL,
                    segments_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    deleted_at TEXT,
                    UNIQUE(project_id, slot)
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id),
                    workspace_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    state TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    error_code TEXT,
                    error_detail TEXT,
                    retry_eligible INTEGER NOT NULL DEFAULT 0,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(workspace_id, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(jobs)")}
            if "error_detail" not in columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN error_detail TEXT")

    def audit(
        self,
        principal: Principal,
        action: str,
        resource_type: str,
        resource_id: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_id(),
                    principal.workspace_id,
                    principal.user_id,
                    action,
                    resource_type,
                    resource_id,
                    json.dumps(metadata or {}, sort_keys=True),
                    utc_now(),
                ),
            )

    def create_project(self, principal: Principal, journal_candidate: str) -> dict[str, object]:
        project_id = new_id()
        created_at = utc_now()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO projects
                   (id, workspace_id, owner_id, journal_candidate, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (project_id, principal.workspace_id, principal.user_id, journal_candidate, created_at),
            )
        self.audit(principal, "project.created", "project", project_id)
        return self.get_project(principal, project_id)

    def _project_row(self, principal: Principal, project_id: str) -> sqlite3.Row:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE id = ? AND workspace_id = ? AND deleted_at IS NULL",
                (project_id, principal.workspace_id),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return cast(sqlite3.Row, row)

    def get_project(self, principal: Principal, project_id: str) -> dict[str, object]:
        row = self._project_row(principal, project_id)
        with self.connect() as connection:
            documents = connection.execute(
                """SELECT id, slot, filename, media_type, byte_size, content_hash,
                          extraction_quality
                   FROM documents
                   WHERE project_id = ? AND workspace_id = ? AND deleted_at IS NULL
                   ORDER BY slot""",
                (project_id, principal.workspace_id),
            ).fetchall()
        return {
            "id": row["id"],
            "journalCandidate": row["journal_candidate"],
            "journal": (
                {
                    "title": row["journal_title"],
                    "issn": row["journal_issn"],
                    "officialDomain": row["journal_domain"],
                }
                if row["journal_confirmed_at"]
                else None
            ),
            "requiredSlots": list(SLOTS),
            "documents": [dict(document) for document in documents],
            "readyForResearch": bool(row["journal_confirmed_at"])
            and {document["slot"] for document in documents} == set(SLOTS),
            "createdAt": row["created_at"],
        }

    def confirm_journal(
        self,
        principal: Principal,
        project_id: str,
        title: str,
        issn: str,
        official_domain: str,
    ) -> dict[str, object]:
        self._project_row(principal, project_id)
        with self.connect() as connection:
            connection.execute(
                """UPDATE projects
                   SET journal_title = ?, journal_issn = ?, journal_domain = ?, journal_confirmed_at = ?
                   WHERE id = ? AND workspace_id = ?""",
                (title, issn, official_domain, utc_now(), project_id, principal.workspace_id),
            )
        self.audit(principal, "journal.confirmed", "project", project_id, {"issn": issn})
        return self.get_project(principal, project_id)

    def store_document(
        self,
        principal: Principal,
        project_id: str,
        slot: DocumentSlot,
        filename: str,
        declared_media_type: str,
        content: bytes,
    ) -> dict[str, object]:
        self._project_row(principal, project_id)
        validation = validate_and_extract(slot, filename, declared_media_type, content)
        digest = hashlib.sha256(content).hexdigest()
        object_key = f"{principal.workspace_id}/{project_id}/{new_id()}"
        object_path = self.object_root / object_key
        object_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(object_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
        except FileExistsError as error:  # pragma: no cover - UUID collision guard
            raise HTTPException(status_code=409, detail="Object collision") from error

        document_id = new_id()
        try:
            with self.connect() as connection:
                connection.execute(
                    "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                    (
                        document_id,
                        project_id,
                        principal.workspace_id,
                        slot,
                        filename,
                        validation["media_type"],
                        len(content),
                        f"sha256:{digest}",
                        object_key,
                        "clean",
                        validation["quality"],
                        json.dumps(validation["segments"], ensure_ascii=False),
                        utc_now(),
                    ),
                )
        except sqlite3.IntegrityError as error:
            object_path.unlink(missing_ok=True)
            raise HTTPException(status_code=409, detail=f"Slot {slot} is already occupied") from error

        self.audit(
            principal,
            "document.ingested",
            "document",
            document_id,
            {"slot": slot, "hash": f"sha256:{digest}"},
        )
        return self.get_project(principal, project_id)

    def start_job(self, principal: Principal, project_id: str, idempotency_key: str) -> dict[str, object]:
        project = self.get_project(principal, project_id)
        if not project["readyForResearch"]:
            raise HTTPException(
                status_code=409,
                detail="Confirm the journal and upload exactly one manuscript and three references",
            )
        with self.connect() as connection:
            existing = connection.execute(
                "SELECT * FROM jobs WHERE workspace_id = ? AND idempotency_key = ?",
                (principal.workspace_id, idempotency_key),
            ).fetchone()
            if existing:
                return job_payload(existing)
            job_id = new_id()
            now = utc_now()
            connection.execute(
                """INSERT INTO jobs
                   (id, project_id, workspace_id, idempotency_key, state, stage, progress,
                    error_code, error_detail, retry_eligible, cancel_requested, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'succeeded', 'ingestion-complete', 100, NULL, NULL, 0, 0, ?, ?)""",
                (job_id, project_id, principal.workspace_id, idempotency_key, now, now),
            )
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        assert row is not None
        self.audit(principal, "job.completed", "job", job_id)
        return job_payload(row)

    def get_job(self, principal: Principal, job_id: str) -> dict[str, object]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE id = ? AND workspace_id = ?",
                (job_id, principal.workspace_id),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return job_payload(row)

    def cancel_job(self, principal: Principal, job_id: str) -> dict[str, object]:
        job = self.get_job(principal, job_id)
        if job["state"] == "succeeded":
            raise HTTPException(status_code=409, detail="Completed jobs cannot be cancelled")
        with self.connect() as connection:
            connection.execute(
                """UPDATE jobs
                   SET state = 'cancelled', cancel_requested = 1, updated_at = ?
                   WHERE id = ? AND workspace_id = ?""",
                (utc_now(), job_id, principal.workspace_id),
            )
        self.audit(principal, "job.cancelled", "job", job_id)
        cancelled = self.get_job(principal, job_id)
        self.delete_source_documents(principal, str(job["projectId"]))
        return cancelled

    def delete_project(self, principal: Principal, project_id: str) -> None:
        self._project_row(principal, project_id)
        with self.connect() as connection:
            objects = connection.execute(
                "SELECT object_key FROM documents WHERE project_id = ? AND workspace_id = ? AND deleted_at IS NULL",
                (project_id, principal.workspace_id),
            ).fetchall()
            analysis_tables_exist = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'analysis_runs'"
            ).fetchone()
            if analysis_tables_exist:
                analysis_rows = connection.execute(
                    "SELECT id, profile_version_id FROM analysis_runs WHERE project_id = ? AND workspace_id = ?",
                    (project_id, principal.workspace_id),
                ).fetchall()
                analysis_ids = [row["id"] for row in analysis_rows]
                profile_version_ids = {row["profile_version_id"] for row in analysis_rows}
                for analysis_id in analysis_ids:
                    objects.extend(
                        connection.execute(
                            "SELECT object_key FROM analysis_artifacts WHERE analysis_id = ? AND workspace_id = ?",
                            (analysis_id, principal.workspace_id),
                        ).fetchall()
                    )
                    recommendation_ids = connection.execute(
                        "SELECT id FROM recommendations WHERE analysis_id = ?", (analysis_id,)
                    ).fetchall()
                    for recommendation in recommendation_ids:
                        connection.execute(
                            "DELETE FROM recommendation_decisions WHERE recommendation_id = ? AND workspace_id = ?",
                            (recommendation["id"], principal.workspace_id),
                        )
                    connection.execute("DELETE FROM analysis_artifacts WHERE analysis_id = ?", (analysis_id,))
                    connection.execute("DELETE FROM recommendations WHERE analysis_id = ?", (analysis_id,))
                    connection.execute("DELETE FROM guide_rules WHERE analysis_id = ?", (analysis_id,))
                    connection.execute("DELETE FROM analysis_runs WHERE id = ?", (analysis_id,))
                for profile_version_id in profile_version_ids:
                    connection.execute(
                        "DELETE FROM journal_source_snapshots WHERE profile_version_id = ?", (profile_version_id,)
                    )
                    is_head = connection.execute(
                        "SELECT 1 FROM journal_profile_heads WHERE version_id = ?", (profile_version_id,)
                    ).fetchone()
                    is_referenced = connection.execute(
                        "SELECT 1 FROM analysis_runs WHERE profile_version_id = ?", (profile_version_id,)
                    ).fetchone()
                    if not is_head and not is_referenced:
                        connection.execute(
                            "UPDATE journal_profile_versions SET supersedes_id = NULL WHERE supersedes_id = ?",
                            (profile_version_id,),
                        )
                        connection.execute("DELETE FROM journal_profile_versions WHERE id = ?", (profile_version_id,))
            connection.execute(
                "DELETE FROM documents WHERE project_id = ? AND workspace_id = ?",
                (project_id, principal.workspace_id),
            )
            connection.execute(
                "DELETE FROM jobs WHERE project_id = ? AND workspace_id = ?",
                (project_id, principal.workspace_id),
            )
            connection.execute(
                "DELETE FROM projects WHERE id = ? AND workspace_id = ?",
                (project_id, principal.workspace_id),
            )
        for item in objects:
            (self.object_root / item["object_key"]).unlink(missing_ok=True)
        self.audit(principal, "project.deleted", "project", project_id)

    def delete_source_documents(self, principal: Principal, project_id: str) -> int:
        """Remove submitted bytes and extracted private text after terminal processing."""
        self._project_row(principal, project_id)
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT object_key FROM documents WHERE project_id = ? AND workspace_id = ?",
                (project_id, principal.workspace_id),
            ).fetchall()
            connection.execute(
                "DELETE FROM documents WHERE project_id = ? AND workspace_id = ?",
                (project_id, principal.workspace_id),
            )
        for row in rows:
            (self.object_root / row["object_key"]).unlink(missing_ok=True)
        self.audit(principal, "documents.ephemeral-deleted", "project", project_id, {"count": str(len(rows))})
        return len(rows)

    def purge_expired(self) -> int:
        cutoff = (datetime.now(UTC) - timedelta(hours=EPHEMERAL_RETENTION_HOURS)).isoformat()
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, workspace_id, owner_id FROM projects WHERE created_at < ? AND deleted_at IS NULL",
                (cutoff,),
            ).fetchall()
        for row in rows:
            self.delete_project(Principal(row["owner_id"], row["workspace_id"]), row["id"])
        return len(rows)

    def reference_texts(self, principal: Principal, project_id: str) -> list[str]:
        """Return workspace-scoped reference text for ephemeral profile derivation."""
        self._project_row(principal, project_id)
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT segments_json FROM documents
                   WHERE project_id = ? AND workspace_id = ? AND slot LIKE 'reference-%' AND deleted_at IS NULL
                   ORDER BY slot""",
                (project_id, principal.workspace_id),
            ).fetchall()
        return ["\n".join(str(segment.get("text", "")) for segment in json.loads(row["segments_json"])) for row in rows]

    def manuscript_record(self, principal: Principal, project_id: str) -> dict[str, object]:
        self._project_row(principal, project_id)
        with self.connect() as connection:
            row = connection.execute(
                """SELECT id, filename, media_type, content_hash, object_key, segments_json
                   FROM documents WHERE project_id = ? AND workspace_id = ?
                   AND slot = 'manuscript' AND deleted_at IS NULL""",
                (project_id, principal.workspace_id),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=409, detail="A validated manuscript is required")
        segments = json.loads(row["segments_json"])
        return {
            "id": row["id"],
            "filename": row["filename"],
            "mediaType": row["media_type"],
            "contentHash": row["content_hash"],
            "objectKey": row["object_key"],
            "text": "\n".join(str(segment.get("text", "")) for segment in segments),
            "anchors": [str(segment.get("anchor", "")) for segment in segments],
            "segments": segments,
        }

    def read_private_object(self, principal: Principal, object_key: str) -> bytes:
        if not object_key.startswith(f"{principal.workspace_id}/"):
            raise HTTPException(status_code=404, detail="Private object not found")
        try:
            return (self.object_root / object_key).read_bytes()
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Private object not found") from error


def validate_and_extract(
    slot: DocumentSlot, filename: str, declared_media_type: str, content: bytes
) -> dict[str, object]:
    if not content:
        raise HTTPException(status_code=422, detail="File is empty")
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 25 MB limit")
    if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in content:
        raise HTTPException(status_code=422, detail="File failed malware scanning")

    is_pdf = content.startswith(b"%PDF-")
    is_docx = content.startswith(b"PK\x03\x04") and _is_docx(content)
    if slot != "manuscript" and not is_pdf:
        raise HTTPException(status_code=415, detail="Reference articles must be valid PDFs")
    if slot == "manuscript" and not (is_pdf or is_docx):
        raise HTTPException(status_code=415, detail="Manuscript must be a valid PDF or DOCX")

    media_type = (
        "application/pdf" if is_pdf else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    if declared_media_type != media_type:
        raise HTTPException(status_code=415, detail="Declared MIME type does not match file signature")

    if is_pdf:
        try:
            reader = PdfReader(BytesIO(content), strict=False)
            if reader.is_encrypted and reader.decrypt("") == 0:
                raise HTTPException(status_code=422, detail="Password-protected PDFs are not supported")
            page_count = len(reader.pages)
        except HTTPException:
            raise
        except (PdfReadError, ValueError, TypeError) as error:
            raise HTTPException(status_code=422, detail="PDF structure is invalid or unreadable") from error
        if page_count == 0:
            raise HTTPException(status_code=422, detail="PDF contains no pages")
        if page_count > MAX_PDF_PAGES:
            raise HTTPException(status_code=422, detail="PDF exceeds the 200-page limit")
        segments = []
        try:
            for index, page in enumerate(reader.pages, 1):
                page_text = _normalize_extracted_text(page.extract_text() or "")
                segments.append({"anchor": f"page:{index}", "text": page_text[:20_000]})
        except (PdfReadError, ValueError, TypeError, KeyError) as error:
            raise HTTPException(status_code=422, detail="PDF text extraction failed") from error
        text = "\n".join(str(segment["text"]) for segment in segments)
    else:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            xml = archive.read("word/document.xml")
        word_namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        try:
            root = ET.fromstring(xml)
            paragraphs = [
                "".join(node.text or "" for node in paragraph.iter(f"{word_namespace}t")).strip()
                for paragraph in root.iter(f"{word_namespace}p")
            ]
        except ET.ParseError:
            # Some minimal but readable DOCX fixtures omit namespace declarations.
            raw_paragraphs = xml.decode("utf-8", errors="ignore").replace("</w:p>", "\n").splitlines()
            paragraphs = [html.unescape(re.sub(r"<[^>]+>", "", paragraph)).strip() for paragraph in raw_paragraphs]
        paragraphs = [paragraph for paragraph in paragraphs if paragraph]
        text = "\n".join(paragraphs)
        segments = [
            {"anchor": f"paragraph:{index}", "text": paragraph[:500]} for index, paragraph in enumerate(paragraphs, 1)
        ] or [{"anchor": "paragraph:1", "text": ""}]

    quality = _text_quality(text)
    if quality < 0.02:
        raise HTTPException(status_code=422, detail="Text extraction quality is too low")
    return {"media_type": media_type, "segments": segments, "quality": round(quality, 3)}


def _normalize_extracted_text(value: str) -> str:
    value = value.replace("\x00", " ").replace("\u00ad", "")
    value = "\n".join(" ".join(line.split()) for line in value.splitlines())
    return value.strip()


def _text_quality(value: str) -> float:
    compact = "".join(value.split())
    if not compact:
        return 0.0
    readable = sum(character.isprintable() for character in compact) / len(compact)
    linguistic = sum(character.isalpha() or character.isdigit() for character in compact) / len(compact)
    volume = min(1.0, len(compact) / 500)
    return volume * readable * linguistic


def _is_docx(content: bytes) -> bool:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_DOCX_ENTRIES:
                return False
            if sum(entry.file_size for entry in entries) > MAX_DOCX_UNCOMPRESSED_BYTES:
                return False
            if any(entry.filename.startswith(("/", "\\")) or ".." in Path(entry.filename).parts for entry in entries):
                return False
            return "word/document.xml" in archive.namelist()
    except zipfile.BadZipFile:
        return False


def job_payload(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": row["id"],
        "projectId": row["project_id"],
        "state": row["state"],
        "stage": row["stage"],
        "progress": row["progress"],
        "errorCode": row["error_code"],
        "errorDetail": row["error_detail"],
        "retryEligible": bool(row["retry_eligible"]),
        "updatedAt": row["updated_at"],
    }
