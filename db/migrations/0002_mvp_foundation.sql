-- PostgreSQL target schema. The local adapter mirrors these tenant predicates in SQLite.
CREATE TABLE workspaces (
  id uuid PRIMARY KEY,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE projects (
  id uuid PRIMARY KEY,
  workspace_id uuid NOT NULL REFERENCES workspaces(id),
  owner_id text NOT NULL,
  journal_candidate text NOT NULL,
  journal_title text,
  journal_issn text,
  journal_domain text,
  journal_confirmed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY projects_workspace_isolation ON projects
USING (workspace_id = current_setting('app.workspace_id')::uuid)
WITH CHECK (workspace_id = current_setting('app.workspace_id')::uuid);

-- Documents, jobs and audit_events repeat workspace_id deliberately so every
-- query and future RLS policy can reject cross-tenant access before joining.
