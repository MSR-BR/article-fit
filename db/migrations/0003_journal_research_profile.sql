-- Immutable shared journal profile history. Raw private document text is forbidden here.
CREATE TABLE journal_profile_versions (
  id uuid PRIMARY KEY,
  journal_issn text NOT NULL,
  version integer NOT NULL CHECK (version > 0),
  status text NOT NULL CHECK (status = 'published'),
  claims_json jsonb NOT NULL,
  evidence_json jsonb NOT NULL,
  limitations_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  supersedes_id uuid REFERENCES journal_profile_versions(id),
  UNIQUE (journal_issn, version)
);

CREATE TABLE journal_profile_heads (
  journal_issn text PRIMARY KEY,
  version_id uuid NOT NULL REFERENCES journal_profile_versions(id),
  version integer NOT NULL CHECK (version > 0)
);

REVOKE UPDATE, DELETE ON journal_profile_versions FROM PUBLIC;

COMMENT ON TABLE journal_profile_versions IS
  'Append-only derived journal knowledge with provenance; never stores private raw text.';
