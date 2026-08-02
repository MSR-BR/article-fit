begin;

alter table jobs
  add column if not exists error_detail text;

comment on column jobs.error_detail is
  'Bounded operational error detail shown to the submitter; purged with the ephemeral project.';

commit;
