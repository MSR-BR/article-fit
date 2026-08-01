# Change 006 — Export and Deployment

Status: `in progress - C6.1 minimal local interface`

## Objective

Deploy the validated MVP as a secure invitation-only pilot with monitored exports, operational controls, rollback, and user-facing limitations.

## Requirements

- Keep the pilot interface intentionally minimal: one multi-file input for three or more orientation articles and one input for the manuscript.
- Require the user to inform the target journal by title, ISSN, or official URL. Orientation articles may be repository versions such as arXiv and must never be treated as sufficient journal-identification evidence.
- Enable an explicit `Iniciar análise` action only after a valid upload package is present.
- During execution, show an accessible progress popup describing the current stage and the remaining stages; allow the user to continue in the background.
- Show outputs in a compact results region on the same page, below upload status, with report and revised-manuscript downloads in DOCX and PDF.

- Provision approved regional infrastructure using reproducible configuration.
- Configure domains/TLS, identity, secrets, database, private storage, queues, workers, backups, retention, observability, quotas, and provider budgets.
- Run compatible migrations and deploy immutable versioned artifacts through staging to pilot.
- Enable feature flags, canary/batch rollout, health/readiness checks, alerting, and rollback.
- Publish privacy/retention notices, acceptable use, source limitations, accessibility/support contact, and “no acceptance guarantee” disclosure.
- Validate production export downloads, signed URL expiry, deletion, audit trail, and disaster recovery without using unapproved sensitive documents.

## Acceptance criteria

- A pilot user completes the supported workflow and downloads all validated deliverables.
- Tenant isolation, private storage, TLS, secret management, backups, retention/deletion, quotas, and alerts are active.
- Deployment and rollback are repeatable; recovery exercises meet approved objectives.
- Release manifest links code, migrations, profile/prompt versions, tests, and known limitations.
- Operational owners can diagnose, pause processing, revoke access, and handle incidents.
- Broader public access remains disabled.

## Files to modify

- `infra/environments/`, deployment/CI workflows, runtime configuration, migration/release manifests.
- Health/observability hooks, feature flags, quotas, operational runbooks, and user-facing policy/help pages.
- Export fixes only if required by validated pilot environment behavior.

## Tests to run

- Infrastructure validation, migration rehearsal, smoke and end-to-end pilot tests.
- TLS/header/storage/authorization/signed-URL/security checks.
- Backup/restore, deletion, provider outage, worker pause/resume, alert, rollback, and disaster-recovery drills.
- Production artifact parity and visual spot checks using approved synthetic data.

## Completion checklist

- [x] C6.1 minimal local upload and results interface implemented.
- [x] C6.2 interface connected to backend orchestration and explicit journal confirmation.
- [x] Pilot hosting architecture proposed in ADR 0004; no external resources provisioned.

- [ ] Hosting/provider/privacy decisions and reviews are approved.
- [ ] Staging release gates pass unchanged in the pilot environment.
- [ ] Infrastructure, observability, budgets, backups, and deletion are verified.
- [ ] Rollback and incident runbooks are exercised.
- [ ] Pilot disclosures/support ownership are active.
- [ ] Release manifest and sign-off are recorded.
