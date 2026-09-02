# Implementation Roadmap

## MVP outcome

An MVP visitor can upload a manuscript and three references without login, confirm a journal, receive evidence-backed journal research, review categorized revision proposals, and download validated DOCX/PDF outputs for up to 24 hours. Uploaded sources are deleted after processing; shared journal profiles improve through versioned derived conclusions without retaining private manuscript material.

## Phase sequence

| Phase | Outcome                                                                                           | Exit gate                                 |
| ----- | ------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| 001   | Repository skeleton, contracts, local stack, CI baseline                                          | Smoke test and quality commands pass      |
| 002   | Secure upload, extraction, jobs, storage, journal confirmation                                    | Private ingestion flow passes end to end  |
| 003   | Article discovery, lawful full-text resolution, official-guide capture, versioned journal profile | Evidence/provenance evaluation passes     |
| 004   | Compliance and editorial analysis, review workflow, DOCX/PDF/report generation                    | Golden-document and integrity checks pass |
| 005   | Security, accessibility, reliability, AI evaluations, expert validation                           | Release thresholds and threat review pass |
| 006   | Staging, operational controls, pilot deployment, rollback                                         | Production-readiness checklist approved   |

## Suggested milestones

- M0 — approve assumptions, providers, privacy/retention, and Change 001.
- M1 — developer foundation and architectural proof points.
- M2 — ingestion and journal-resolution vertical slice.
- M3 — evidence acquisition and first versioned journal profile.
- M4 — manuscript analysis and reviewable recommendation ledger.
- M5 — document exports and expert-reviewed evaluation set.
- M6 — open MVP with server-side abuse controls, monitoring, and a manual incident path.

## Future backlog (not MVP)

- Additional languages; collaborative author/reviewer workflows; native Word tracked changes after fidelity validation; journal portfolio comparisons; submission packaging; domain-specific reporting checklists; institutional SSO; billing; and publisher partnerships.

No date estimate is asserted until Change 001 decisions and team capacity are known.
