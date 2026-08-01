# Change 002 retention and deletion

- Pilot retention: 30 days from project creation.
- User deletion: immediate removal of original private objects; project and document metadata are tombstoned for audit consistency.
- Scheduled deletion: `python -m journal_matcher_worker.main --purge-expired` applies the same deletion path.
- Audit events contain no document text and remain available for security review.
- Shared journal knowledge is not created in Change 002, so no shared-derived data survives deletion.
