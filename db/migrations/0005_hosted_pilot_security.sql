-- Article Fit hosted pilot hardening.
-- This migration is forward-only and safe to rerun during setup rehearsal.

create extension if not exists pgcrypto;
create extension if not exists pgmq;

create table if not exists workspace_members (
  workspace_id uuid not null references workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'member' check (role in ('owner', 'member')),
  created_at timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

create table if not exists documents (
  id uuid primary key,
  project_id uuid not null references projects(id) on delete cascade,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  slot text not null check (slot in ('manuscript', 'reference-1', 'reference-2', 'reference-3')),
  filename text not null,
  media_type text not null check (media_type in (
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  )),
  byte_size bigint not null check (byte_size > 0 and byte_size <= 26214400),
  content_hash text not null check (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  object_key text not null unique,
  malware_status text not null check (malware_status in ('pending', 'clean', 'rejected')),
  extraction_quality double precision not null check (extraction_quality between 0 and 1),
  segments_json jsonb not null,
  created_at timestamptz not null default now(),
  deleted_at timestamptz,
  unique (project_id, slot)
);

create table if not exists jobs (
  id uuid primary key,
  project_id uuid not null references projects(id) on delete cascade,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  idempotency_key text not null,
  state text not null check (state in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
  stage text not null,
  progress integer not null check (progress between 0 and 100),
  error_code text,
  retry_eligible boolean not null default false,
  cancel_requested boolean not null default false,
  attempt_count integer not null default 0 check (attempt_count >= 0),
  available_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, idempotency_key)
);

create table if not exists audit_events (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  actor_id text not null,
  action text not null,
  resource_type text not null,
  resource_id text not null,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists projects_workspace_created_idx on projects (workspace_id, created_at desc);
create index if not exists documents_workspace_project_idx on documents (workspace_id, project_id);
create index if not exists jobs_claim_idx on jobs (state, available_at, created_at) where state = 'queued';
create index if not exists jobs_workspace_project_idx on jobs (workspace_id, project_id, created_at desc);
create index if not exists audit_events_workspace_created_idx on audit_events (workspace_id, created_at desc);
create index if not exists analysis_runs_workspace_project_idx on analysis_runs (workspace_id, project_id);
create index if not exists recommendation_decisions_workspace_idx on recommendation_decisions (workspace_id);
create index if not exists analysis_artifacts_workspace_idx on analysis_artifacts (workspace_id, analysis_id);

alter table workspaces enable row level security;
alter table workspace_members enable row level security;
alter table projects enable row level security;
alter table documents enable row level security;
alter table jobs enable row level security;
alter table audit_events enable row level security;
alter table journal_profile_versions enable row level security;
alter table journal_profile_heads enable row level security;
alter table analysis_runs enable row level security;
alter table guide_rules enable row level security;
alter table recommendations enable row level security;
alter table recommendation_decisions enable row level security;
alter table analysis_artifacts enable row level security;

drop policy if exists projects_workspace_isolation on projects;
drop policy if exists analysis_workspace_isolation on analysis_runs;
drop policy if exists decision_workspace_isolation on recommendation_decisions;
drop policy if exists artifact_workspace_isolation on analysis_artifacts;
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

create policy workspaces_member_read on workspaces for select to authenticated
using (exists (
  select 1 from workspace_members membership
  where membership.workspace_id = workspaces.id and membership.user_id = (select auth.uid())
));

create policy memberships_self_read on workspace_members for select to authenticated
using (user_id = (select auth.uid()));

create policy projects_member_read on projects for select to authenticated
using (exists (
  select 1 from workspace_members membership
  where membership.workspace_id = projects.workspace_id and membership.user_id = (select auth.uid())
));

create policy documents_member_read on documents for select to authenticated
using (exists (
  select 1 from workspace_members membership
  where membership.workspace_id = documents.workspace_id and membership.user_id = (select auth.uid())
));

create policy jobs_member_read on jobs for select to authenticated
using (exists (
  select 1 from workspace_members membership
  where membership.workspace_id = jobs.workspace_id and membership.user_id = (select auth.uid())
));

create policy audit_events_member_read on audit_events for select to authenticated
using (exists (
  select 1 from workspace_members membership
  where membership.workspace_id = audit_events.workspace_id and membership.user_id = (select auth.uid())
));

create policy shared_profile_versions_read on journal_profile_versions for select to authenticated using (true);
create policy shared_profile_heads_read on journal_profile_heads for select to authenticated using (true);

create policy analysis_runs_member_read on analysis_runs for select to authenticated
using (exists (
  select 1 from workspace_members membership
  where membership.workspace_id = analysis_runs.workspace_id and membership.user_id = (select auth.uid())
));

create policy guide_rules_member_read on guide_rules for select to authenticated
using (exists (
  select 1 from analysis_runs run
  join workspace_members membership on membership.workspace_id = run.workspace_id
  where run.id = guide_rules.analysis_id and membership.user_id = (select auth.uid())
));

create policy recommendations_member_read on recommendations for select to authenticated
using (exists (
  select 1 from analysis_runs run
  join workspace_members membership on membership.workspace_id = run.workspace_id
  where run.id = recommendations.analysis_id and membership.user_id = (select auth.uid())
));

create policy recommendation_decisions_member_read on recommendation_decisions for select to authenticated
using (exists (
  select 1 from workspace_members membership
  where membership.workspace_id = recommendation_decisions.workspace_id
    and membership.user_id = (select auth.uid())
));

create policy analysis_artifacts_member_read on analysis_artifacts for select to authenticated
using (exists (
  select 1 from workspace_members membership
  where membership.workspace_id = analysis_artifacts.workspace_id and membership.user_id = (select auth.uid())
));

revoke all on all tables in schema public from anon;
grant select on workspaces, workspace_members, projects, documents, jobs, audit_events,
  journal_profile_versions, journal_profile_heads, analysis_runs, guide_rules, recommendations,
  recommendation_decisions, analysis_artifacts to authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('manuscripts', 'manuscripts', false, 26214400, array[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]),
  ('artifacts', 'artifacts', false, 26214400, array[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/json'
  ])
on conflict (id) do update set
  public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists private_workspace_objects_read on storage.objects;
create policy private_workspace_objects_read on storage.objects for select to authenticated
using (
  bucket_id in ('manuscripts', 'artifacts')
  and exists (
    select 1 from workspace_members membership
    where membership.workspace_id::text = (storage.foldername(name))[1]
      and membership.user_id = (select auth.uid())
  )
);

select pgmq.create('analysis_jobs')
where not exists (
  select 1 from pgmq.meta where queue_name = 'analysis_jobs'
);
