# Change 005 — Testing and Validation

Status: `validation — automated/local gates passed; expert and staging gates pending`

## Approved scope decisions

- Freeze automated and expert-review thresholds before evaluating the Change 005 release candidate.
- Use synthetic fixtures only in the repository; licensed third-party manuscripts are excluded until storage rights are documented case by case.
- Local CI may prove deterministic, security, privacy, accessibility, performance-budget, failure, backup/restore, deletion, and artifact gates.
- Blind expert scoring and production-like staging drills require named human reviewers and deployed infrastructure. They remain blocking release-sign-off gates and cannot be marked passed by automated tests.
- Change 005 may correct defects needed to satisfy already-approved MVP safeguards, but cannot add deployment behavior owned by Change 006.

## Objective

Demonstrate that the MVP is safe, evidence-grounded, usable, reliable, and ready for a controlled deployment.

## Requirements

- Implement the complete `shared/testing-strategy.md` matrix in CI/staging.
- Build a licensed/synthetic benchmark spanning journals, article types, DOCX/PDF complexity, unavailable sources, and conflicting guidance.
- Establish expert-review rubrics and thresholds before scoring release candidates.
- Perform threat modeling, dependency/container scanning, authorization testing, privacy/deletion validation, accessibility audit, load tests, and failure drills.
- Measure citation correctness, unsupported-claim rate, scientific invariant preservation, recommendation usefulness, document fidelity, latency, and cost.
- Triage failures with traceable test evidence; no threshold is relaxed silently.

## Acceptance criteria

- All release gates in the shared testing and anti-hallucination policies pass.
- Zero open critical/high security or privacy defects.
- Zero fabricated identifiers or unsupported journal requirements in the fixed release benchmark.
- Supported documents show no silent content loss; known limitations are prominent.
- Expert quality thresholds, inter-reviewer agreement method, sample composition, and residual risks are documented.
- Backup/restore, deletion, retry, provider outage, and rollback drills succeed in staging.

## Files to modify

- Unit/contract/integration/e2e/security/accessibility/performance/evaluation suites.
- Synthetic/licensed fixture manifests and golden artifacts.
- CI workflows, staging configuration, quality dashboards, threat model, runbooks, and release evidence.
- Bug fixes strictly necessary to meet already-approved MVP requirements.

## Tests to run

- Entire automated suite and fixed AI evaluation suite.
- SAST/dependency/container/secret scans and manual authorization review.
- Accessibility audit, load/soak tests, chaos/failure drills, restore/deletion exercises.
- Blind expert review and artifact visual inspection across the supported matrix.

## Completion checklist

- [x] Benchmark rights and provenance are documented.
- [x] Rubrics/thresholds were frozen before final evaluation.
- [ ] All required suites and operational drills pass — local suites/drills pass; staging drills remain pending.
- [ ] Expert review and accessibility/security findings are resolved or accepted explicitly — automated accessibility/security gates pass; blind expert review remains pending.
- [x] Residual risks and supported matrix are published.
- [ ] Release candidate is signed off for controlled deployment.
