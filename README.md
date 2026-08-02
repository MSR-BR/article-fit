# Article Fit

Article Fit is an evidence-first AI-assisted manuscript preparation pilot. The hosted workflow accepts a target journal, three reference articles, and one manuscript; researches recent literature and official journal guidance; learns a versioned editorial profile; produces evidence-linked recommendations; and exports a revision report plus revised DOCX/PDF artifacts.

The production pilot uses Vercel for the minimal web interface, Cloud Run for the Python API and durable worker, and one secured Supabase project for named authentication, private storage, metadata, and the job queue. It remains invitation-only and makes no guarantee of journal acceptance.

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

The local API test path defaults to bearer token `local-invite-token` and stores metadata plus private objects below `/tmp/journal-matcher`. The hosted path requires Supabase Auth, validates the user and workspace membership in both the Vercel proxy and Python API, and never exposes the service-role key to the browser. Configure the values documented in `.env.example` before running either mode. Replace the example provider email with a monitored operational address; Crossref, OpenAlex, and Unpaywall require identifiable, rate-limited use.

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
