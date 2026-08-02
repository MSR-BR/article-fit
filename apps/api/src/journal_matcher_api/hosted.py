"""Small server-only Supabase boundary for hosted persistence and queues."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException

from journal_matcher_api.foundation import (
    EPHEMERAL_RETENTION_HOURS,
    DocumentSlot,
    Principal,
    new_id,
    utc_now,
    validate_and_extract,
)
from journal_matcher_api.journal_research import (
    OFFICIAL_TYPES,
    Evidence,
    durable_profile_payload,
    merge_profile_memory,
    validate_claim,
)
from journal_matcher_api.manuscript_analysis import Decision, now_iso, scope_analysis_records, stable_id


@dataclass(frozen=True)
class SupabaseSettings:
    url: str
    service_role_key: str
    publishable_key: str | None = None

    def __post_init__(self) -> None:
        if not self.url.startswith("https://"):
            raise ValueError("SUPABASE_URL must use HTTPS")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")


class SupabaseHttpClient:
    """Use PostgREST and Storage without exposing privileged credentials."""

    def __init__(self, settings: SupabaseSettings, timeout: float = 30.0) -> None:
        self._base_url = settings.url.rstrip("/")
        self._key = settings.service_role_key
        self._publishable_key = settings.publishable_key
        self._timeout = timeout

    def verify_user(self, access_token: str) -> dict[str, Any]:
        """Validate a hosted access token against Supabase Auth."""
        if not self._publishable_key:
            raise HTTPException(status_code=503, detail="Hosted authentication is not configured")
        request = Request(
            f"{self._base_url}/auth/v1/user",
            headers={
                "apikey": self._publishable_key,
                "Authorization": f"Bearer {access_token}",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:  # noqa: S310 - fixed trusted base URL
                payload = json.loads(response.read())
        except HTTPError as error:
            if error.code in {401, 403}:
                raise HTTPException(status_code=401, detail="Invalid or expired session") from None
            raise HTTPException(status_code=502, detail=f"Hosted authentication failed ({error.code})") from None
        except (TimeoutError, URLError) as error:
            raise HTTPException(status_code=503, detail="Hosted authentication is temporarily unavailable") from error
        except json.JSONDecodeError as error:
            raise HTTPException(status_code=502, detail="Hosted authentication returned invalid JSON") from error
        if not isinstance(payload, dict):
            raise HTTPException(status_code=502, detail="Hosted authentication returned an invalid user")
        return payload

    def table(
        self,
        name: str,
        *,
        method: str = "GET",
        query: dict[str, str] | None = None,
        payload: object | None = None,
        prefer: str | None = None,
    ) -> object:
        return self._json_request(
            f"/rest/v1/{quote(name, safe='')}", method=method, query=query, payload=payload, prefer=prefer
        )

    def rpc(self, function: str, payload: dict[str, object], *, schema: str = "public") -> object:
        return self._json_request(
            f"/rest/v1/rpc/{quote(function, safe='')}",
            method="POST",
            payload=payload,
            extra_headers={"Accept-Profile": schema, "Content-Profile": schema},
        )

    def upload(self, bucket: str, object_key: str, content: bytes, media_type: str) -> None:
        self._request(
            f"/storage/v1/object/{quote(bucket, safe='')}/{quote(object_key, safe='/')}",
            method="POST",
            body=content,
            content_type=media_type,
            extra_headers={"x-upsert": "false"},
        )

    def download(self, bucket: str, object_key: str) -> bytes:
        return self._request(
            f"/storage/v1/object/authenticated/{quote(bucket, safe='')}/{quote(object_key, safe='/')}",
            method="GET",
            storage_missing_is_not_found=True,
        )

    def delete_objects(self, bucket: str, object_keys: list[str]) -> None:
        for object_key in object_keys:
            try:
                self._request(
                    f"/storage/v1/object/{quote(bucket, safe='')}/{quote(object_key, safe='/')}",
                    method="DELETE",
                    storage_missing_is_not_found=True,
                )
            except HTTPException as error:
                if error.status_code != 404:
                    raise

    def _json_request(
        self,
        path: str,
        *,
        method: str,
        query: dict[str, str] | None = None,
        payload: object | None = None,
        prefer: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> object:
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        raw = self._request(
            path,
            method=method,
            query=query,
            body=body,
            content_type="application/json",
            extra_headers={**(extra_headers or {}), **({"Prefer": prefer} if prefer else {})},
        )
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise HTTPException(status_code=502, detail="Hosted persistence returned invalid JSON") from error

    def _request(
        self,
        path: str,
        *,
        method: str,
        query: dict[str, str] | None = None,
        body: bytes | None = None,
        content_type: str | None = None,
        extra_headers: dict[str, str] | None = None,
        storage_missing_is_not_found: bool = False,
    ) -> bytes:
        suffix = f"?{urlencode(query)}" if query else ""
        headers = {"apikey": self._key, "Authorization": f"Bearer {self._key}", **(extra_headers or {})}
        if content_type:
            headers["Content-Type"] = content_type
        request = Request(f"{self._base_url}{path}{suffix}", data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self._timeout) as response:  # noqa: S310 - fixed trusted base URL
                return cast(bytes, response.read())
        except HTTPError as error:
            # Do not include response bodies: upstream errors can echo private data.
            if error.code in {401, 403}:
                raise HTTPException(status_code=503, detail="Hosted persistence authorization failed") from None
            if error.code == 404 or (storage_missing_is_not_found and error.code == 400):
                raise HTTPException(status_code=404, detail="Hosted resource not found") from None
            if error.code == 409:
                raise HTTPException(status_code=409, detail="Hosted persistence conflict") from None
            raise HTTPException(status_code=502, detail=f"Hosted persistence failed ({error.code})") from None
        except (TimeoutError, URLError) as error:
            raise HTTPException(status_code=503, detail="Hosted persistence is temporarily unavailable") from error


def require_rows(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise HTTPException(status_code=502, detail="Hosted persistence returned an invalid row set")
    return value


class HostedFoundationStore:
    """Supabase-backed equivalent of the local foundation store."""

    def __init__(self, client: SupabaseHttpClient) -> None:
        self.client = client

    def is_workspace_member(self, user_id: str, workspace_id: str) -> bool:
        rows = require_rows(
            self.client.table(
                "workspace_members",
                query={
                    "select": "workspace_id",
                    "workspace_id": f"eq.{workspace_id}",
                    "user_id": f"eq.{user_id}",
                    "limit": "1",
                },
            )
        )
        return bool(rows)

    def audit(
        self,
        principal: Principal,
        action: str,
        resource_type: str,
        resource_id: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.client.table(
            "audit_events",
            method="POST",
            payload={
                "id": new_id(),
                "workspace_id": principal.workspace_id,
                "actor_id": principal.user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "metadata_json": metadata or {},
                "created_at": utc_now(),
            },
        )

    def create_project(self, principal: Principal, journal_candidate: str) -> dict[str, object]:
        self.client.table(
            "workspaces",
            method="POST",
            payload={"id": principal.workspace_id},
            prefer="resolution=ignore-duplicates",
        )
        project_id = new_id()
        self.client.table(
            "projects",
            method="POST",
            payload={
                "id": project_id,
                "workspace_id": principal.workspace_id,
                "owner_id": principal.user_id,
                "journal_candidate": journal_candidate,
                "created_at": utc_now(),
            },
        )
        self.audit(principal, "project.created", "project", project_id)
        return self.get_project(principal, project_id)

    def _project_row(self, principal: Principal, project_id: str) -> dict[str, Any]:
        rows = require_rows(
            self.client.table(
                "projects",
                query={
                    "select": "*",
                    "id": f"eq.{project_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "deleted_at": "is.null",
                    "limit": "1",
                },
            )
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Project not found")
        return rows[0]

    def get_project(self, principal: Principal, project_id: str) -> dict[str, object]:
        row = self._project_row(principal, project_id)
        documents = require_rows(
            self.client.table(
                "documents",
                query={
                    "select": "id,slot,filename,media_type,byte_size,content_hash,extraction_quality",
                    "project_id": f"eq.{project_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "deleted_at": "is.null",
                    "order": "slot.asc",
                },
            )
        )
        return {
            "id": row["id"],
            "journalCandidate": row["journal_candidate"],
            "journal": (
                {
                    "title": row["journal_title"],
                    "issn": row["journal_issn"],
                    "officialDomain": row["journal_domain"],
                }
                if row.get("journal_confirmed_at")
                else None
            ),
            "requiredSlots": ["manuscript", "reference-1", "reference-2", "reference-3"],
            "documents": documents,
            "readyForResearch": bool(row.get("journal_confirmed_at"))
            and {str(document["slot"]) for document in documents}
            == {"manuscript", "reference-1", "reference-2", "reference-3"},
            "createdAt": row["created_at"],
        }

    def confirm_journal(
        self, principal: Principal, project_id: str, title: str, issn: str, official_domain: str
    ) -> dict[str, object]:
        self._project_row(principal, project_id)
        self.client.table(
            "projects",
            method="PATCH",
            query={"id": f"eq.{project_id}", "workspace_id": f"eq.{principal.workspace_id}"},
            payload={
                "journal_title": title,
                "journal_issn": issn,
                "journal_domain": official_domain,
                "journal_confirmed_at": utc_now(),
            },
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
        media_type = str(validation["media_type"])
        self.client.upload("manuscripts", object_key, content, media_type)
        document_id = new_id()
        try:
            self.client.table(
                "documents",
                method="POST",
                payload={
                    "id": document_id,
                    "project_id": project_id,
                    "workspace_id": principal.workspace_id,
                    "slot": slot,
                    "filename": filename,
                    "media_type": media_type,
                    "byte_size": len(content),
                    "content_hash": f"sha256:{digest}",
                    "object_key": object_key,
                    "malware_status": "clean",
                    "extraction_quality": validation["quality"],
                    "segments_json": validation["segments"],
                    "created_at": utc_now(),
                },
            )
        except HTTPException:
            self.client.delete_objects("manuscripts", [object_key])
            raise
        self.audit(principal, "document.ingested", "document", document_id, {"slot": slot})
        return self.get_project(principal, project_id)

    def start_job(
        self,
        principal: Principal,
        project_id: str,
        idempotency_key: str,
        workflow_message: dict[str, object] | None = None,
    ) -> dict[str, object]:
        project = self.get_project(principal, project_id)
        documents = project.get("documents", [])
        complete_slots = isinstance(documents, list) and {str(item.get("slot")) for item in documents} == {
            "manuscript",
            "reference-1",
            "reference-2",
            "reference-3",
        }
        if (workflow_message is None and not project["readyForResearch"]) or (
            workflow_message is not None and not complete_slots
        ):
            raise HTTPException(
                status_code=409,
                detail="Confirm the journal and upload exactly one manuscript and three references",
            )
        existing = require_rows(
            self.client.table(
                "jobs",
                query={
                    "select": "*",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "idempotency_key": f"eq.{idempotency_key}",
                    "limit": "1",
                },
            )
        )
        if existing:
            return hosted_job_payload(existing[0])
        job_id, now = new_id(), utc_now()
        rows = require_rows(
            self.client.table(
                "jobs",
                method="POST",
                payload={
                    "id": job_id,
                    "project_id": project_id,
                    "workspace_id": principal.workspace_id,
                    "idempotency_key": idempotency_key,
                    "state": "queued",
                    "stage": "awaiting-worker",
                    "progress": 0,
                    "created_at": now,
                    "updated_at": now,
                },
                prefer="return=representation",
            )
        )
        self.client.rpc(
            "send",
            {
                "queue_name": "analysis_jobs",
                "message": {"job_id": job_id, **(workflow_message or {})},
                "sleep_seconds": 0,
            },
            schema="pgmq_public",
        )
        self.audit(principal, "job.queued", "job", job_id)
        return hosted_job_payload(rows[0])

    def read_queue(self, batch_size: int = 1, visibility_seconds: int = 60) -> list[dict[str, Any]]:
        return require_rows(
            self.client.rpc(
                "read",
                {"queue_name": "analysis_jobs", "sleep_seconds": visibility_seconds, "n": batch_size},
                schema="pgmq_public",
            )
        )

    def delete_queue_message(self, message_id: int) -> None:
        self.client.rpc(
            "delete",
            {"queue_name": "analysis_jobs", "message_id": message_id},
            schema="pgmq_public",
        )

    def worker_job(self, job_id: str) -> dict[str, Any] | None:
        rows = require_rows(self.client.table("jobs", query={"select": "*", "id": f"eq.{job_id}", "limit": "1"}))
        return rows[0] if rows else None

    def update_worker_job(
        self,
        job_id: str,
        *,
        state: str,
        stage: str,
        progress: int,
        error_code: str | None = None,
        error_detail: str | None = None,
        retry_eligible: bool = False,
        increment_attempt: bool = False,
    ) -> dict[str, Any]:
        current = self.worker_job(job_id)
        if current is None:
            raise HTTPException(status_code=404, detail="Job not found")
        payload: dict[str, object] = {
            "state": state,
            "stage": stage,
            "progress": progress,
            "error_code": error_code,
            "error_detail": error_detail,
            "retry_eligible": retry_eligible,
            "updated_at": utc_now(),
        }
        if increment_attempt:
            payload["attempt_count"] = int(current.get("attempt_count", 0)) + 1
        rows = require_rows(
            self.client.table(
                "jobs",
                method="PATCH",
                query={"id": f"eq.{job_id}"},
                payload=payload,
                prefer="return=representation",
            )
        )
        if not rows:
            raise HTTPException(status_code=409, detail="Job state update failed")
        return rows[0]

    def get_job(self, principal: Principal, job_id: str) -> dict[str, object]:
        rows = require_rows(
            self.client.table(
                "jobs",
                query={
                    "select": "*",
                    "id": f"eq.{job_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "limit": "1",
                },
            )
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Job not found")
        return hosted_job_payload(rows[0])

    def cancel_job(self, principal: Principal, job_id: str) -> dict[str, object]:
        job = self.get_job(principal, job_id)
        if job["state"] == "succeeded":
            raise HTTPException(status_code=409, detail="Completed jobs cannot be cancelled")
        self.client.table(
            "jobs",
            method="PATCH",
            query={"id": f"eq.{job_id}", "workspace_id": f"eq.{principal.workspace_id}"},
            payload={"state": "cancelled", "cancel_requested": True, "updated_at": utc_now()},
        )
        self.audit(principal, "job.cancelled", "job", job_id)
        cancelled = self.get_job(principal, job_id)
        self.delete_source_documents(principal, str(job["projectId"]))
        return cancelled

    def reference_texts(self, principal: Principal, project_id: str) -> list[str]:
        self._project_row(principal, project_id)
        rows = require_rows(
            self.client.table(
                "documents",
                query={
                    "select": "segments_json",
                    "project_id": f"eq.{project_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "slot": "like.reference-%",
                    "deleted_at": "is.null",
                    "order": "slot.asc",
                },
            )
        )
        return ["\n".join(str(segment.get("text", "")) for segment in row["segments_json"]) for row in rows]

    def manuscript_record(self, principal: Principal, project_id: str) -> dict[str, object]:
        self._project_row(principal, project_id)
        rows = require_rows(
            self.client.table(
                "documents",
                query={
                    "select": "id,filename,media_type,content_hash,object_key,segments_json",
                    "project_id": f"eq.{project_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "slot": "eq.manuscript",
                    "deleted_at": "is.null",
                    "limit": "1",
                },
            )
        )
        if not rows:
            raise HTTPException(status_code=409, detail="A validated manuscript is required")
        row, segments = rows[0], rows[0]["segments_json"]
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
        bucket = "artifacts" if "/artifacts/" in object_key else "manuscripts"
        return self.client.download(bucket, object_key)

    def delete_project(self, principal: Principal, project_id: str) -> None:
        self._project_row(principal, project_id)
        document_rows = require_rows(
            self.client.table(
                "documents",
                query={
                    "select": "object_key",
                    "project_id": f"eq.{project_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                },
            )
        )
        analysis_rows = require_rows(
            self.client.table(
                "analysis_runs",
                query={
                    "select": "id,profile_version_id",
                    "project_id": f"eq.{project_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                },
            )
        )
        analysis_ids = [str(row["id"]) for row in analysis_rows]
        profile_version_ids = {str(row["profile_version_id"]) for row in analysis_rows}
        artifact_rows: list[dict[str, Any]] = []
        recommendation_rows: list[dict[str, Any]] = []
        if analysis_ids:
            joined_ids = ",".join(analysis_ids)
            artifact_rows = require_rows(
                self.client.table(
                    "analysis_artifacts",
                    query={
                        "select": "object_key",
                        "analysis_id": f"in.({joined_ids})",
                        "workspace_id": f"eq.{principal.workspace_id}",
                    },
                )
            )
            recommendation_rows = require_rows(
                self.client.table(
                    "recommendations",
                    query={"select": "id", "analysis_id": f"in.({joined_ids})"},
                )
            )
            self.client.delete_objects("manuscripts", [str(row["object_key"]) for row in document_rows])
            if artifact_rows:
                self.client.delete_objects("artifacts", [str(row["object_key"]) for row in artifact_rows])
            recommendation_ids = [str(row["id"]) for row in recommendation_rows]
            if recommendation_ids:
                self.client.table(
                    "recommendation_decisions",
                    method="DELETE",
                    query={
                        "recommendation_id": f"in.({','.join(recommendation_ids)})",
                        "workspace_id": f"eq.{principal.workspace_id}",
                    },
                )
            for table in ("analysis_artifacts", "recommendations", "guide_rules"):
                self.client.table(table, method="DELETE", query={"analysis_id": f"in.({joined_ids})"})
            self.client.table(
                "analysis_runs",
                method="DELETE",
                query={"id": f"in.({joined_ids})", "workspace_id": f"eq.{principal.workspace_id}"},
            )
            for profile_version_id in profile_version_ids:
                self.client.table(
                    "journal_source_snapshots",
                    method="DELETE",
                    query={"profile_version_id": f"eq.{profile_version_id}"},
                )
                head_rows = require_rows(
                    self.client.table(
                        "journal_profile_heads",
                        query={"select": "version_id", "version_id": f"eq.{profile_version_id}", "limit": "1"},
                    )
                )
                reference_rows = require_rows(
                    self.client.table(
                        "analysis_runs",
                        query={"select": "id", "profile_version_id": f"eq.{profile_version_id}", "limit": "1"},
                    )
                )
                if not head_rows and not reference_rows:
                    self.client.table(
                        "journal_profile_versions",
                        method="PATCH",
                        query={"supersedes_id": f"eq.{profile_version_id}"},
                        payload={"supersedes_id": None},
                    )
                    self.client.table(
                        "journal_profile_versions", method="DELETE", query={"id": f"eq.{profile_version_id}"}
                    )
        if not analysis_ids:
            self.client.delete_objects("manuscripts", [str(row["object_key"]) for row in document_rows])
        self.client.table(
            "documents",
            method="DELETE",
            query={"project_id": f"eq.{project_id}", "workspace_id": f"eq.{principal.workspace_id}"},
        )
        self.client.table(
            "projects",
            method="DELETE",
            query={"id": f"eq.{project_id}", "workspace_id": f"eq.{principal.workspace_id}"},
        )
        self.audit(principal, "project.deleted", "project", project_id)

    def delete_source_documents(self, principal: Principal, project_id: str) -> int:
        """Remove submitted Storage objects and all extracted private document rows."""
        self._project_row(principal, project_id)
        rows = require_rows(
            self.client.table(
                "documents",
                query={
                    "select": "object_key",
                    "project_id": f"eq.{project_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                },
            )
        )
        self.client.delete_objects("manuscripts", [str(row["object_key"]) for row in rows])
        self.client.table(
            "documents",
            method="DELETE",
            query={"project_id": f"eq.{project_id}", "workspace_id": f"eq.{principal.workspace_id}"},
        )
        self.audit(
            principal,
            "documents.ephemeral-deleted",
            "project",
            project_id,
            {"count": str(len(rows))},
        )
        return len(rows)

    def purge_expired(self, workspace_id: str | None = None) -> int:
        cutoff = (datetime.now(UTC) - timedelta(hours=EPHEMERAL_RETENTION_HOURS)).isoformat()
        query = {
            "select": "id,workspace_id,owner_id",
            "created_at": f"lt.{cutoff}",
            "deleted_at": "is.null",
        }
        if workspace_id is not None:
            query["workspace_id"] = f"eq.{workspace_id}"
        rows = require_rows(self.client.table("projects", query=query))
        for row in rows:
            self.delete_project(Principal(str(row["owner_id"]), str(row["workspace_id"])), str(row["id"]))
        return len(rows)


def hosted_job_payload(row: dict[str, Any]) -> dict[str, object]:
    return {
        "id": row["id"],
        "projectId": row["project_id"],
        "state": row["state"],
        "stage": row["stage"],
        "progress": row["progress"],
        "errorCode": row.get("error_code"),
        "errorDetail": row.get("error_detail"),
        "retryEligible": bool(row.get("retry_eligible", False)),
        "updatedAt": row["updated_at"],
    }


class HostedJournalProfileRepository:
    """Immutable shared journal-profile history in Supabase Postgres."""

    def __init__(self, client: SupabaseHttpClient) -> None:
        self.client = client

    def migrate(self) -> None:
        return None

    def publish(
        self,
        journal_issn: str,
        evidence: list[Evidence],
        claims: list[dict[str, object]],
        limitations: list[str],
        expected_version: int,
    ) -> dict[str, object]:
        if limitations:
            raise HTTPException(status_code=409, detail="Degraded research cannot publish a shared profile")
        evidence_by_id = {item.source_id: item for item in evidence}
        for claim in claims:
            validate_claim(claim, evidence_by_id)
        heads = require_rows(
            self.client.table(
                "journal_profile_heads",
                query={"select": "version_id,version", "journal_issn": f"eq.{journal_issn}", "limit": "1"},
            )
        )
        current = int(heads[0]["version"]) if heads else 0
        if current != expected_version:
            raise HTTPException(status_code=409, detail="Journal profile was concurrently updated")
        shared_evidence, durable_claims = durable_profile_payload(evidence, claims)
        if heads:
            previous = self.get(str(heads[0]["version_id"]))
            shared_evidence, durable_claims = merge_profile_memory(
                cast(list[dict[str, object]], previous["evidence"]),
                cast(list[dict[str, object]], previous["claims"]),
                shared_evidence,
                durable_claims,
            )
        version = current + 1
        version_id = hashlib.sha256(
            json.dumps([journal_issn, version, shared_evidence, durable_claims], sort_keys=True).encode()
        ).hexdigest()[:32]
        created_at = utc_now()
        self.client.table(
            "journal_profile_versions",
            method="POST",
            payload={
                "id": version_id,
                "journal_issn": journal_issn,
                "version": version,
                "status": "published",
                "claims_json": durable_claims,
                "evidence_json": shared_evidence,
                "limitations_json": [],
                "created_at": created_at,
                "supersedes_id": heads[0]["version_id"] if heads else None,
            },
        )
        self.client.table(
            "journal_profile_heads",
            method="POST",
            payload={"journal_issn": journal_issn, "version_id": version_id, "version": version},
            prefer="resolution=merge-duplicates",
        )
        snapshots = [
            {
                "profile_version_id": version_id,
                "source_id": item.source_id,
                "source_type": item.source_type,
                "content": item.content,
                "content_hash": item.content_hash,
            }
            for item in evidence
            if item.source_type in OFFICIAL_TYPES
        ]
        if snapshots:
            self.client.table("journal_source_snapshots", method="POST", payload=snapshots)
        return self.get(version_id)

    def current_version(self, journal_issn: str) -> int:
        rows = require_rows(
            self.client.table(
                "journal_profile_heads",
                query={"select": "version", "journal_issn": f"eq.{journal_issn}", "limit": "1"},
            )
        )
        return int(rows[0]["version"]) if rows else 0

    def delete_snapshots(self, version_id: str) -> None:
        self.client.table(
            "journal_source_snapshots",
            method="DELETE",
            query={"profile_version_id": f"eq.{version_id}"},
        )

    def official_snapshots(self, version_id: str) -> list[dict[str, str]]:
        self.get(version_id)
        rows = require_rows(
            self.client.table(
                "journal_source_snapshots",
                query={
                    "select": "source_id,source_type,content,content_hash",
                    "profile_version_id": f"eq.{version_id}",
                    "order": "source_type.asc",
                },
            )
        )
        return [{key: str(value) for key, value in row.items()} for row in rows]

    def get(self, version_id: str) -> dict[str, object]:
        rows = require_rows(
            self.client.table(
                "journal_profile_versions",
                query={"select": "*", "id": f"eq.{version_id}", "limit": "1"},
            )
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Journal profile version not found")
        row = rows[0]
        return {
            "id": row["id"],
            "journalIssn": row["journal_issn"],
            "version": row["version"],
            "status": row["status"],
            "claims": row["claims_json"],
            "evidence": row["evidence_json"],
            "limitations": row["limitations_json"],
            "createdAt": row["created_at"],
            "supersedesId": row.get("supersedes_id"),
        }


class HostedAnalysisRepository:
    """Workspace-scoped analysis, decisions, and artifact metadata."""

    def __init__(self, client: SupabaseHttpClient) -> None:
        self.client = client

    def migrate(self) -> None:
        return None

    def create(
        self,
        principal: Principal,
        project_id: str,
        profile_version_id: str,
        manuscript_hash: str,
        invariants: dict[str, list[str]],
        rules: list[dict[str, object]],
        recommendations: list[dict[str, object]],
        limitations: list[str],
    ) -> dict[str, object]:
        analysis_id = stable_id(principal.workspace_id, project_id, profile_version_id, manuscript_hash)
        scoped_rules = scope_analysis_records(analysis_id, "guide-rule", rules)
        scoped_recommendations = scope_analysis_records(analysis_id, "recommendation", recommendations)
        existing = require_rows(
            self.client.table(
                "analysis_runs",
                query={
                    "select": "id",
                    "id": f"eq.{analysis_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "limit": "1",
                },
            )
        )
        if not existing:
            self.client.table(
                "analysis_runs",
                method="POST",
                payload={
                    "id": analysis_id,
                    "project_id": project_id,
                    "workspace_id": principal.workspace_id,
                    "profile_version_id": profile_version_id,
                    "manuscript_hash": manuscript_hash,
                    "invariant_json": invariants,
                    "limitations_json": limitations,
                    "status": "review",
                    "created_at": now_iso(),
                },
                prefer="resolution=ignore-duplicates",
            )
        if scoped_rules:
            self.client.table(
                "guide_rules",
                method="POST",
                payload=[
                    {"id": str(rule["id"]), "analysis_id": analysis_id, "rule_json": rule} for rule in scoped_rules
                ],
                prefer="resolution=ignore-duplicates",
            )
        if scoped_recommendations:
            self.client.table(
                "recommendations",
                method="POST",
                payload=[
                    {"id": str(item["id"]), "analysis_id": analysis_id, "recommendation_json": item}
                    for item in scoped_recommendations
                ],
                prefer="resolution=ignore-duplicates",
            )
        return self.get(principal, analysis_id)

    def get(self, principal: Principal, analysis_id: str) -> dict[str, object]:
        runs = require_rows(
            self.client.table(
                "analysis_runs",
                query={
                    "select": "*",
                    "id": f"eq.{analysis_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "limit": "1",
                },
            )
        )
        if not runs:
            raise HTTPException(status_code=404, detail="Analysis not found")
        rules = require_rows(
            self.client.table("guide_rules", query={"select": "rule_json", "analysis_id": f"eq.{analysis_id}"})
        )
        recommendation_rows = require_rows(
            self.client.table(
                "recommendations",
                query={"select": "id,recommendation_json", "analysis_id": f"eq.{analysis_id}"},
            )
        )
        recommendation_ids = [str(row["id"]) for row in recommendation_rows]
        decisions: list[dict[str, Any]] = []
        if recommendation_ids:
            decisions = require_rows(
                self.client.table(
                    "recommendation_decisions",
                    query={
                        "select": "recommendation_id,decision,modified_text,created_at",
                        "recommendation_id": f"in.({','.join(recommendation_ids)})",
                        "workspace_id": f"eq.{principal.workspace_id}",
                        "order": "created_at.desc",
                    },
                )
            )
        latest = {str(item["recommendation_id"]): item for item in reversed(decisions)}
        recommendations: list[dict[str, object]] = []
        for row in recommendation_rows:
            item = dict(cast(dict[str, object], row["recommendation_json"]))
            decision = latest.get(str(row["id"]))
            if decision:
                item["decision"] = decision["decision"]
                item["modifiedText"] = decision.get("modified_text")
                item["decidedAt"] = decision["created_at"]
            recommendations.append(item)
        artifacts = require_rows(
            self.client.table(
                "analysis_artifacts",
                query={
                    "select": "id,kind,content_hash,validation_json,created_at",
                    "analysis_id": f"eq.{analysis_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "order": "kind.asc",
                },
            )
        )
        run = runs[0]
        return {
            "id": run["id"],
            "projectId": run["project_id"],
            "profileVersionId": run["profile_version_id"],
            "status": run["status"],
            "limitations": run["limitations_json"],
            "rules": [row["rule_json"] for row in rules],
            "recommendations": recommendations,
            "artifacts": artifacts,
            "createdAt": run["created_at"],
        }

    def latest_for_project(self, principal: Principal, project_id: str) -> dict[str, object]:
        rows = require_rows(
            self.client.table(
                "analysis_runs",
                query={
                    "select": "id",
                    "project_id": f"eq.{project_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "order": "created_at.desc",
                    "limit": "1",
                },
            )
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return self.get(principal, str(rows[0]["id"]))

    def add_ai_review(
        self,
        principal: Principal,
        analysis_id: str,
        recommendations: list[dict[str, object]],
        limitations: list[str],
    ) -> dict[str, object]:
        analysis = self.get(principal, analysis_id)
        previous = analysis["limitations"]
        if not isinstance(previous, list):
            raise HTTPException(status_code=500, detail="Stored analysis limitations are invalid")
        scoped_recommendations = scope_analysis_records(analysis_id, "recommendation", recommendations)
        if scoped_recommendations:
            self.client.table(
                "recommendations",
                method="POST",
                payload=[
                    {"id": str(item["id"]), "analysis_id": analysis_id, "recommendation_json": item}
                    for item in scoped_recommendations
                ],
                prefer="resolution=ignore-duplicates",
            )
        self.client.table(
            "analysis_runs",
            method="PATCH",
            query={"id": f"eq.{analysis_id}", "workspace_id": f"eq.{principal.workspace_id}"},
            payload={"limitations_json": list(dict.fromkeys([*previous, *limitations]))},
        )
        return self.get(principal, analysis_id)

    def decide(
        self,
        principal: Principal,
        analysis_id: str,
        recommendation_id: str,
        decision: Decision,
        modified_text: str | None,
    ) -> dict[str, object]:
        analysis = self.get(principal, analysis_id)
        recommendation_items = analysis["recommendations"]
        if not isinstance(recommendation_items, list):
            raise HTTPException(status_code=500, detail="Stored recommendation set is invalid")
        recommendation = next(
            (item for item in recommendation_items if isinstance(item, dict) and item.get("id") == recommendation_id),
            None,
        )
        if recommendation is None:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        if decision == "modified" and not modified_text:
            raise HTTPException(status_code=422, detail="Modified decisions require replacement text")
        if recommendation.get("scientificImpact") and decision == "accepted":
            raise HTTPException(
                status_code=409, detail="Scientific-impact recommendations require an explicit modified text"
            )
        self.client.table(
            "recommendation_decisions",
            method="POST",
            payload={
                "id": new_id(),
                "recommendation_id": recommendation_id,
                "workspace_id": principal.workspace_id,
                "decision": decision,
                "modified_text": modified_text,
                "created_at": now_iso(),
            },
        )
        return self.get(principal, analysis_id)

    def artifact_key(self, principal: Principal, analysis_id: str, kind: str) -> str:
        self.get(principal, analysis_id)
        rows = require_rows(
            self.client.table(
                "analysis_artifacts",
                query={
                    "select": "object_key",
                    "analysis_id": f"eq.{analysis_id}",
                    "workspace_id": f"eq.{principal.workspace_id}",
                    "kind": f"eq.{kind}",
                    "limit": "1",
                },
            )
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Artifact not found")
        return str(rows[0]["object_key"])

    def store_artifacts(
        self,
        principal: Principal,
        analysis_id: str,
        artifacts: dict[str, bytes],
        validation: dict[str, object],
    ) -> dict[str, object]:
        self.get(principal, analysis_id)
        uploaded: list[str] = []
        try:
            for kind, content in artifacts.items():
                object_key = f"{principal.workspace_id}/artifacts/{analysis_id}/{kind}"
                media_type = (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    if kind.endswith(".docx")
                    else "application/pdf"
                    if kind.endswith(".pdf")
                    else "application/json"
                )
                self.client.upload("artifacts", object_key, content, media_type)
                uploaded.append(object_key)
                self.client.table(
                    "analysis_artifacts",
                    method="POST",
                    payload={
                        "id": stable_id(analysis_id, kind),
                        "analysis_id": analysis_id,
                        "workspace_id": principal.workspace_id,
                        "kind": kind,
                        "object_key": object_key,
                        "content_hash": f"sha256:{hashlib.sha256(content).hexdigest()}",
                        "validation_json": validation,
                        "created_at": now_iso(),
                    },
                    prefer="resolution=merge-duplicates",
                )
            self.client.table(
                "analysis_runs",
                method="PATCH",
                query={"id": f"eq.{analysis_id}", "workspace_id": f"eq.{principal.workspace_id}"},
                payload={"status": "artifacts-ready"},
            )
        except HTTPException:
            self.client.delete_objects("artifacts", uploaded)
            raise
        return self.get(principal, analysis_id)
