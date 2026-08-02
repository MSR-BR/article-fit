"""One-shot durable workflow worker."""

import argparse
import asyncio
import json
import os
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from journal_matcher_api.foundation import FoundationStore, Principal
from journal_matcher_api.hosted import HostedFoundationStore, SupabaseHttpClient, SupabaseSettings
from journal_matcher_api.main import WorkflowRequest, execute_project_workflow
from pydantic import ValidationError

from journal_matcher_worker import __version__


def health_payload() -> dict[str, str]:
    """Return the worker health contract without external side effects."""
    return {"service": "worker", "status": "ok", "version": __version__}


def hosted_store() -> HostedFoundationStore:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("Hosted worker requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    return HostedFoundationStore(SupabaseHttpClient(SupabaseSettings(url, key)))


def process_message(store: HostedFoundationStore, queue_row: dict[str, Any]) -> bool:
    message_id = queue_row.get("msg_id")
    message = queue_row.get("message")
    if not isinstance(message_id, int) or not isinstance(message, dict):
        raise RuntimeError("Queue returned an invalid message envelope")
    job_id = message.get("job_id")
    workflow_payload = message.get("workflow")
    if not isinstance(job_id, str) or not isinstance(workflow_payload, dict):
        store.delete_queue_message(message_id)
        return False
    job = store.worker_job(job_id)
    if job is None or job.get("state") in {"cancelled", "succeeded", "failed"}:
        if job is not None and job.get("state") in {"cancelled", "failed"}:
            store.delete_source_documents(
                Principal(user_id="article-fit-worker", workspace_id=str(job["workspace_id"])),
                str(job["project_id"]),
            )
        store.delete_queue_message(message_id)
        return True
    claimed = store.update_worker_job(
        job_id,
        state="running",
        stage="journal-research",
        progress=10,
        increment_attempt=True,
    )
    try:
        request = WorkflowRequest.model_validate(workflow_payload)
        principal = Principal(user_id="article-fit-worker", workspace_id=str(claimed["workspace_id"]))
        result = asyncio.run(execute_project_workflow(str(claimed["project_id"]), request, principal, store))
    except (HTTPException, ValidationError, RuntimeError, ValueError) as error:
        attempts = int(claimed.get("attempt_count", 1))
        terminal = attempts >= 3
        error_code = f"workflow-{getattr(error, 'status_code', 'failed')}"
        store.update_worker_job(
            job_id,
            state="failed" if terminal else "queued",
            stage="failed" if terminal else "awaiting-retry",
            progress=int(claimed.get("progress", 10)),
            error_code=error_code,
            retry_eligible=not terminal,
        )
        if terminal:
            store.delete_source_documents(
                Principal(user_id="article-fit-worker", workspace_id=str(claimed["workspace_id"])),
                str(claimed["project_id"]),
            )
            store.delete_queue_message(message_id)
        return False
    if result.get("state") != "succeeded":
        raise RuntimeError("Workflow did not produce a successful terminal result")
    store.update_worker_job(job_id, state="succeeded", stage="artifacts-ready", progress=100)
    store.delete_queue_message(message_id)
    return True


def process_batch(batch_size: int) -> int:
    store = hosted_store()
    remaining = batch_size
    failures = 0
    while remaining:
        messages = store.read_queue(batch_size=remaining, visibility_seconds=5)
        if not messages:
            break
        for message in messages:
            if not process_message(store, message):
                failures += 1
            remaining -= 1
        if failures and remaining:
            time.sleep(5)
    print(json.dumps({"processed": batch_size - remaining, "failures": failures}, sort_keys=True))
    return 1 if failures else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run a one-shot health check or report the intentionally idle shell."""
    parser = argparse.ArgumentParser(description="Journal Matcher worker shell")
    parser.add_argument("--health-check", action="store_true")
    parser.add_argument("--purge-expired", action="store_true")
    parser.add_argument("--process-batch", action="store_true")
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args(argv)

    if args.health_check:
        print(json.dumps(health_payload(), sort_keys=True))
        return 0

    if args.purge_expired:
        if os.getenv("JOURNAL_MATCHER_PERSISTENCE", "local") == "supabase":
            count = hosted_store().purge_expired()
        else:
            data_root = Path(os.getenv("JOURNAL_MATCHER_DATA_ROOT", "/tmp/journal-matcher"))
            count = FoundationStore(data_root / "metadata.sqlite3", data_root / "objects").purge_expired()
        print(json.dumps({"purgedProjects": count}, sort_keys=True))
        return 0

    if args.process_batch:
        if args.batch_size < 1 or args.batch_size > 10:
            parser.error("--batch-size must be between 1 and 10")
        return process_batch(args.batch_size)

    print("Journal Matcher ingestion worker is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
