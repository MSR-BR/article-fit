-- Harden the Supabase-managed pgmq_public Queue API for server-only use.
-- Prerequisite: enable "Expose Queues via PostgREST" in Queue settings.

create table if not exists journal_source_snapshots (
  profile_version_id uuid not null references journal_profile_versions(id) on delete cascade,
  source_id text not null,
  source_type text not null check (source_type in ('official-guide', 'official-scope')),
  content text not null,
  content_hash text not null check (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  primary key (profile_version_id, source_id)
);

alter table journal_source_snapshots enable row level security;
revoke all on journal_source_snapshots from anon, authenticated;

do $$
begin
  if to_regprocedure('pgmq_public.send(text,jsonb,integer)') is null
     or to_regprocedure('pgmq_public.read(text,integer,integer)') is null
     or to_regprocedure('pgmq_public.delete(text,bigint)') is null then
    raise exception 'Enable Expose Queues via PostgREST before applying migration 0006';
  end if;
end;
$$;

revoke execute on function pgmq_public.send(text, jsonb, integer) from public, anon, authenticated;
revoke execute on function pgmq_public.read(text, integer, integer) from public, anon, authenticated;
revoke execute on function pgmq_public.delete(text, bigint) from public, anon, authenticated;

grant usage on schema pgmq_public to service_role;
grant execute on function pgmq_public.send(text, jsonb, integer) to service_role;
grant execute on function pgmq_public.read(text, integer, integer) to service_role;
grant execute on function pgmq_public.delete(text, bigint) to service_role;
