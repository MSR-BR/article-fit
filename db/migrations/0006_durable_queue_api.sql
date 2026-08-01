-- Harden the Supabase-managed pgmq_public Queue API for server-only use.
-- Prerequisite: enable "Expose Queues via PostgREST" in Queue settings.

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
