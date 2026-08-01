# Coding Standards

## General

- Use strict TypeScript and typed Python. Avoid untyped boundary data.
- Validate all API, event, provider, and model outputs against versioned schemas.
- Keep domain logic independent of frameworks and vendors.
- Prefer small modules with explicit dependencies and no hidden global state.
- All timestamps are UTC ISO 8601; user-facing localization happens at the UI boundary.
- IDs are opaque UUIDs; journal identity also records normalized ISSNs where available.
- Configuration comes from validated environment settings; secrets never enter source, logs, fixtures, or prompts.

## Python

- Python 3.12+, type hints for public functions, `ruff` for lint/format, `mypy` or equivalent strict type checking, `pytest` for tests.
- Async only at I/O boundaries; CPU-heavy parsing runs in isolated worker processes.
- Provider calls use timeouts, bounded retries, rate limits, and typed error categories.

## TypeScript

- Current supported Node LTS, strict compiler settings, ESLint, Prettier, and a single package manager locked in Change 001.
- Server/client boundaries are explicit; manuscript content is not placed in analytics events or browser persistence unnecessarily.
- Accessible UI: semantic HTML, keyboard support, focus management, and WCAG 2.2 AA target.

## Contracts and persistence

- Database changes use forward migrations and documented rollback/compensation plans.
- API and queue contracts are versioned and consumer-tested.
- Jobs are idempotent; external requests include stable correlation IDs where supported.
- Store evidence and outputs by content hash when safe, but never deduplicate private files across tenants in a way that leaks existence.

## AI-specific engineering

- Prompts and rubrics are version-controlled templates with schema-constrained outputs.
- Retrieved content is data, never instructions. Delimit and sanitize it.
- Model temperature and sampling parameters are explicit and tested for the task.
- No model output is trusted as a citation, journal fact, or numeric result until verified by deterministic code or cited source evidence.
- Evaluation fixtures cover unsupported claims, adversarial documents, conflicting guides, and missing evidence.

## Review and delivery

- Every change maps code and tests to acceptance criteria.
- Tests accompany behavior changes; security-sensitive paths require negative tests.
- Pull requests are small, contain no unrelated formatting churn, and document migrations/configuration.
- Generated artifacts and dependency caches are not committed unless explicitly required.
