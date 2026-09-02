from pathlib import Path

MIGRATION = Path("db/migrations/0005_hosted_pilot_security.sql")
QUEUE_MIGRATION = Path("db/migrations/0006_durable_queue_api.sql")
OPEN_MVP_MIGRATION = Path("db/migrations/0007_open_mvp_ephemeral_storage.sql")


def test_hosted_migration_keeps_storage_private_and_bounded() -> None:
    sql = MIGRATION.read_text()

    assert "('manuscripts', 'manuscripts', false, 26214400" in sql
    assert "('artifacts', 'artifacts', false, 26214400" in sql
    assert "private_workspace_objects_read" in sql
    assert "membership.workspace_id::text = (storage.foldername(name))[1]" in sql


def test_hosted_migration_scopes_private_rows_by_workspace_membership() -> None:
    sql = MIGRATION.read_text()

    private_tables = (
        "workspaces",
        "workspace_members",
        "projects",
        "documents",
        "jobs",
        "audit_events",
        "analysis_runs",
        "guide_rules",
        "recommendations",
        "recommendation_decisions",
        "analysis_artifacts",
    )
    for table in private_tables:
        assert f"alter table {table} enable row level security;" in sql

    assert "membership.user_id = (select auth.uid())" in sql
    assert "revoke all on all tables in schema public from anon;" in sql
    assert "TO authenticated\nUSING (true)" not in sql


def test_hosted_migration_creates_durable_queue_without_browser_grants() -> None:
    sql = MIGRATION.read_text()

    assert "create extension if not exists pgmq;" in sql
    assert "pgmq.create('analysis_jobs')" in sql
    assert "grant" not in "\n".join(line for line in sql.splitlines() if "pgmq" in line).lower()


def test_queue_rpc_is_service_role_only() -> None:
    sql = QUEUE_MIGRATION.read_text().lower()

    assert "security definer" not in sql
    assert "pgmq_public.send(text,jsonb,integer)" in sql
    assert "revoke execute on function pgmq_public.read(text, integer, integer) from public, anon, authenticated" in sql
    assert "grant execute on function pgmq_public.delete(text, bigint) to service_role" in sql
    assert "alter table journal_source_snapshots enable row level security" in sql
    assert "revoke all on journal_source_snapshots from anon, authenticated" in sql


def test_open_mvp_closes_legacy_browser_access_and_marks_ephemeral_rows() -> None:
    sql = OPEN_MVP_MIGRATION.read_text().lower()

    assert "drop policy if exists private_workspace_objects_read on storage.objects" in sql
    assert "analysis_artifacts from anon, authenticated" in sql
    assert "projects_ephemeral_purge_idx" in sql
    assert "hard-delete at terminal processing or within 24 hours" in sql
    assert "never store uploaded bytes, private text, filenames, or private hashes" in sql
    assert "delete from storage.objects" not in sql
