# Change 010 — Brand and Pilot Bootstrap

Status: `completed`

## Objective

Rename the public product to Article Fit and bootstrap an invitation-only preview using the owner-approved GitHub, Vercel, and Supabase accounts without exposing secrets or treating local-development persistence as production-ready.

## Requirements

- Use Article Fit as the public product name while retaining internal package and route identifiers until a dedicated compatibility migration is justified.
- Publish to a private GitHub repository under the authenticated `MSR-BR` account.
- Link the web project to the `msr-br` Vercel scope and preserve server-only secrets.
- Provision or connect the Supabase project named `article fit` under `marioreis@id.uff.br` in São Paulo where available.
- Do not expose service-role credentials, use public buckets, or deploy SQLite/local filesystem as production persistence.
- Deploy a preview first; production promotion requires successful smoke checks and explicit reporting of backend limitations.

## Acceptance criteria

- Local brand surfaces and generated-product headings say Article Fit.
- Full tests, lint, typing, build, and secret scan pass.
- GitHub commit and push succeed to the intended private repository.
- Vercel project is linked to the intended scope and preview is inspectable.
- Supabase linkage is verified by project reference and key names only; secret values remain undisclosed.
- Any unprovisioned backend component is clearly reported rather than represented as deployed.

## Files to modify

- Public UI, metadata, generated-product labels, README, specifications, environment/deployment configuration, and validation records.

## Tests to run

- Python and web quality suites, production web build, secret scan, Git status/diff review, preview health and page smoke checks.

## Completion checklist

- [x] Public brand renamed to Article Fit.
- [x] Supabase project connected and verified in Production, Preview, and Development.
- [x] Private GitHub repository created, committed, pushed, and draft PR opened.
- [x] Vercel project linked and corrected monorepo preview deployed in `gru1`.
- [x] Preview page and `/api/health` smoke checks pass.

## Validation record

- Preview deployment: `dpl_A8z3m173eTuHF2d1kytAgwychrjD` (`READY`).
- Node.js 24 preview deployment: `dpl_4dBcxAdMV6r9rhBo1YxtEgea62wV` (`READY`).
- Public application shell and web health endpoint respond correctly.
- Supabase environment bindings resolve to the approved project reference `qbjhtdalhjcsmujntoni`; values remain encrypted and undisclosed.
- The processing API and worker are not deployed, so end-to-end manuscript analysis is not yet available in the hosted preview.
