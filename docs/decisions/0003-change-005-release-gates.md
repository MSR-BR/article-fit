# Decision 0003 — Change 005 release gates

Status: accepted

Date: 2026-07-31

## Decision

Change 005 freezes its benchmark, automated thresholds, expert rubric, and release semantics before scoring. Repository fixtures are synthetic and contain no personal or licensed third-party content.

Automated local gates may be reported as passed only with reproducible evidence. Blind expert review and staging-only operational drills are independent blocking gates. If those external gates have not occurred, the change remains in validation and the release candidate is not signed off for controlled deployment.

No threshold may be weakened after seeing a result without a new versioned decision record explaining the failure, risk, and approval.
