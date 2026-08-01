# Article Fit

Article Fit is an evidence-first AI-assisted manuscript preparation project. Changes 001–003 provide runnable web, API, and worker foundations, an invitation-only local ingestion pilot, and evidence-backed journal research/profile creation. The research stage discovers three recent works by confirmed ISSN, seeks lawful open versions, snapshots official scope/author guidance, and publishes only complete, provenance-validated journal profiles.

Manuscript comparison, rewriting, and final export are deliberately not implemented yet.

## Prerequisites

- Node.js 24.18.0 LTS and npm 10 or 11
- Python 3.13.14 (or Docker for the Python services)
- Docker with Compose for PostgreSQL, Redis, and MinIO

## Setup

```bash
cp .env.example .env
npm ci
python3.13 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

Start local dependencies:

```bash
npm run infra:up
```

Run the application shells in separate terminals:

```bash
npm run dev:web
npm run dev:api
npm run dev:worker
```

- Web: `http://localhost:3000`
- Web health: `http://localhost:3000/api/health`
- API health: `http://localhost:8000/health`
- Worker check: `npm run health:worker`

The local pilot defaults to bearer token `local-invite-token`, generates a workspace UUID in the web interface, and stores metadata plus private objects below `/tmp/journal-matcher`. Configure the `JOURNAL_MATCHER_*` values from `.env.example` before any shared or deployed use. Replace the example provider email with a monitored operational address; Crossref, OpenAlex, and Unpaywall require identifiable, rate-limited use. SQLite, local filesystem storage, synchronous research orchestration, bounded extraction, and the EICAR-only malware adapter are development providers; they are not the production security architecture.

## Quality commands

```bash
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
npm run check:boundaries
npm run check:secrets
npm run audit:production
npm run test:containers
npm run scan:images
```

Python commands require Python 3.13 and the dev dependencies. Exact-runtime suites can also run in Docker using `npm run test:python:docker` and `npm run test:javascript:docker`. Change-specific evidence is recorded in `docs/validation/`.

## Specification workflow

Read [.specs/README.md](.specs/README.md) before changing behavior. Each numbered change must be approved before implementation. Never use private or copyright-restricted manuscripts as committed fixtures.
