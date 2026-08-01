# Article Fit — Specification System

Status: Changes 001–004 completed. Change 005 is in validation with external gates pending. Change 006 remains draft.

This directory is the source of truth for the product. Work must follow the change order in `changes/` and may begin only after the applicable change is approved.

## Reading order

1. `shared/project-rules.md`
2. `shared/assumptions.md`
3. `shared/architecture.md`
4. `shared/citation-rules.md`
5. `shared/anti-hallucination-policy.md`
6. `shared/output-format.md`
7. `shared/coding-standards.md`
8. `shared/roadmap.md`
9. The relevant file under `changes/`

## Change lifecycle

`draft -> approved -> in-progress -> validation -> completed`

- A change is not approved merely because its specification exists.
- Scope changes require updating the specification before code.
- Completion requires every acceptance criterion and checklist item to be evidenced.
- Changes 001–004 are completed. Change 005 was approved and is in validation; Change 006 must not begin without explicit user approval.

## Planned changes

| Change | Purpose                                                   | Depends on |
| ------ | --------------------------------------------------------- | ---------- |
| 001    | Create the application skeleton and developer tooling     | Approval   |
| 002    | Implement the secure MVP foundation and ingestion         | 001        |
| 003    | Acquire journal evidence and build a journal profile      | 002        |
| 004    | Analyze the manuscript and generate revision deliverables | 003        |
| 005    | Validate quality, safety, citations, and exports          | 004        |
| 006    | Package and deploy a controlled pilot                     | 005        |
