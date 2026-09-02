# Ephemeral source and product retention

Change 013 supersedes the provisional 30-day policy from Change 002.

- Uploaded manuscript/reference objects and their extracted text are private, temporary processing inputs.
- Terminal success deletes all source objects and `documents` rows immediately after validated artifacts exist.
- Cancellation deletes those sources immediately. A failed asynchronous workflow keeps them only while retries remain and deletes them after the final failed attempt.
- Official guide/scope page snapshots are temporary and deleted after deterministic rule extraction.
- Revised DOCX/PDF/report products remain private and downloadable only until the project reaches 24 hours of age.
- The safety purge `python3.13 -m journal_matcher_worker.main --purge-expired` hard-deletes expired artifact objects and all private per-run database rows through the same application boundary.
- Storage objects are deleted through the Supabase Storage API, never with SQL against `storage.objects`.
- The only durable cross-run record is the journal profile: derived conclusions, official/public provenance, aggregate sample counts, confidence, timestamps, and revision lineage.
- Audit events contain no document text or filenames.

The purge job must run at least hourly in production. A missed purge is an operational incident because 24 hours is a maximum, not a target.
