# Change 005 operational drills

## Local deterministic drills

- Backup/restore: take a SQLite online backup and copy the private object tree; open a new `FoundationStore` from the restored paths and verify the project plus every object hash.
- Deletion: delete a project through the authenticated API; require metadata tombstones and zero retained project objects.
- Retry/idempotency: submit the same idempotency key twice and require one job identity.
- Provider outage: inject bounded provider failures and require an explicit degraded/error response without profile publication.
- Rollback simulation: restore the pre-change database/object snapshot into a separate root and run read-only integrity checks. The active environment is never overwritten by the drill.

## Staging-only drills

Before controlled deployment, operators must exercise managed-database point-in-time restore, object-store version restore, queue redrive, deployment rollback, expired signed downloads, alert delivery, and incident communications in the actual staging stack. Record timestamps, owners, recovery-point/recovery-time observations, and evidence links. Local SQLite/filesystem results do not satisfy these staging gates.
