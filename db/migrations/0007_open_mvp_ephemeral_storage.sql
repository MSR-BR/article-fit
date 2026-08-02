-- Change 013: open MVP with server-only data access and ephemeral private files.
-- The Vercel server proxy and Cloud Run services use service_role. Browsers do
-- not receive a Supabase credential, so legacy authenticated read paths close.

drop policy if exists workspaces_member_read on workspaces;
drop policy if exists memberships_self_read on workspace_members;
drop policy if exists projects_member_read on projects;
drop policy if exists documents_member_read on documents;
drop policy if exists jobs_member_read on jobs;
drop policy if exists audit_events_member_read on audit_events;
drop policy if exists shared_profile_versions_read on journal_profile_versions;
drop policy if exists shared_profile_heads_read on journal_profile_heads;
drop policy if exists analysis_runs_member_read on analysis_runs;
drop policy if exists guide_rules_member_read on guide_rules;
drop policy if exists recommendations_member_read on recommendations;
drop policy if exists recommendation_decisions_member_read on recommendation_decisions;
drop policy if exists analysis_artifacts_member_read on analysis_artifacts;
drop policy if exists private_workspace_objects_read on storage.objects;

revoke all on workspaces, workspace_members, projects, documents, jobs, audit_events,
  journal_profile_versions, journal_profile_heads, journal_source_snapshots,
  analysis_runs, guide_rules, recommendations, recommendation_decisions,
  analysis_artifacts from anon, authenticated;

create index if not exists projects_ephemeral_purge_idx
  on projects (created_at)
  where deleted_at is null;

create index if not exists artifacts_ephemeral_purge_idx
  on analysis_artifacts (created_at);

comment on table documents is
  'Ephemeral source metadata and extracted text; hard-delete at terminal processing or within 24 hours.';
comment on table analysis_artifacts is
  'Ephemeral generated-product metadata; hard-delete with its project within 24 hours.';
comment on table journal_profile_versions is
  'Durable journal-level derived conclusions only; never store uploaded bytes, private text, filenames, or private hashes.';
