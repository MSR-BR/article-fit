# Deployment Strategy

## Environments

- Local: containerized dependencies and synthetic fixtures.
- Preview/CI: ephemeral application environment with mock/sandbox providers and no production manuscripts.
- Staging: production-like private environment for licensed evaluation documents.
- Production pilot: invitation-only, least-privilege access, explicit data terms, and conservative quotas.

## Deployable units

- Web service.
- API service.
- Worker service with separately scalable queues for ingestion, research, analysis, and export.
- Managed PostgreSQL, private object storage, queue, secret manager, and observability backend.

## Delivery controls

- Reproducible pinned builds, software bill of materials, dependency and image scanning, signed artifacts where supported.
- CI runs lint, types, unit, contract, integration, migration, and security checks.
- Database migrations use expand/contract sequencing; deploy workers and API compatibly with old and new contracts.
- Feature flags gate provider use, shared-profile publication, and new analysis templates.
- Canary or small-batch rollout for workers; automatic halt on error, cost, or validation-rate thresholds.
- Rollback application images; use compensating migrations rather than destructive rollback.

## Operations

- Dashboards and alerts for job failures, queue age, provider errors, token/cost budgets, validation failures, storage growth, and suspicious access.
- Encrypted backups with tested point-in-time recovery.
- Retention/deletion jobs with auditable completion and failed-deletion alerts.
- Incident response covers data exposure, corrupted exports, unsupported recommendations, provider compromise, and source/license complaints.
- Provider outage behavior is explicit: retry, switch only to an approved adapter, or return a degraded diagnostic.

## Pre-production requirements

- Resolve the open hosting, region, model, provider, retention, and authentication decisions.
- Complete privacy impact, threat-model, publisher/provider terms, and accessibility reviews.
- Define recovery objectives, availability target, concurrency quota, maximum cost per job, and support ownership.
- Run a limited expert-supervised pilot before broader availability.
