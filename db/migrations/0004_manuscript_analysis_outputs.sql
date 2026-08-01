CREATE TABLE analysis_runs (
  id uuid PRIMARY KEY,
  project_id uuid NOT NULL REFERENCES projects(id),
  workspace_id uuid NOT NULL REFERENCES workspaces(id),
  profile_version_id uuid NOT NULL REFERENCES journal_profile_versions(id),
  manuscript_hash text NOT NULL,
  invariant_json jsonb NOT NULL,
  limitations_json jsonb NOT NULL,
  status text NOT NULL CHECK (status IN ('review', 'artifacts-ready')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, project_id, profile_version_id, manuscript_hash)
);

CREATE TABLE guide_rules (
  id uuid PRIMARY KEY,
  analysis_id uuid NOT NULL REFERENCES analysis_runs(id),
  rule_json jsonb NOT NULL
);

CREATE TABLE recommendations (
  id uuid PRIMARY KEY,
  analysis_id uuid NOT NULL REFERENCES analysis_runs(id),
  recommendation_json jsonb NOT NULL
);

CREATE TABLE recommendation_decisions (
  id uuid PRIMARY KEY,
  recommendation_id uuid NOT NULL REFERENCES recommendations(id),
  workspace_id uuid NOT NULL REFERENCES workspaces(id),
  decision text NOT NULL CHECK (decision IN ('accepted', 'rejected', 'modified')),
  modified_text text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE analysis_artifacts (
  id uuid PRIMARY KEY,
  analysis_id uuid NOT NULL REFERENCES analysis_runs(id),
  workspace_id uuid NOT NULL REFERENCES workspaces(id),
  kind text NOT NULL,
  object_key text NOT NULL,
  content_hash text NOT NULL,
  validation_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (analysis_id, kind)
);

ALTER TABLE analysis_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY analysis_workspace_isolation ON analysis_runs
USING (workspace_id = current_setting('app.workspace_id')::uuid)
WITH CHECK (workspace_id = current_setting('app.workspace_id')::uuid);

ALTER TABLE recommendation_decisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY decision_workspace_isolation ON recommendation_decisions
USING (workspace_id = current_setting('app.workspace_id')::uuid)
WITH CHECK (workspace_id = current_setting('app.workspace_id')::uuid);

ALTER TABLE analysis_artifacts ENABLE ROW LEVEL SECURITY;
CREATE POLICY artifact_workspace_isolation ON analysis_artifacts
USING (workspace_id = current_setting('app.workspace_id')::uuid)
WITH CHECK (workspace_id = current_setting('app.workspace_id')::uuid);
