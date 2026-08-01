# Change 005 security and privacy review

Reviewed: 2026-07-31

## Automated and manual coverage

- Workspace authorization is enforced on projects, analyses, decisions, artifacts, and downloads; cross-workspace reads return `404`.
- Artifact downloads require the invitation token and workspace header. Signed URLs are not used in the local pilot and therefore have no expiry surface; production download design remains Change 006.
- URL acquisition uses HTTPS, official-domain restrictions, DNS/private-network rejection, bounded responses, retry limits, and untrusted-content handling.
- Upload validation covers signatures, MIME agreement, byte/page limits, low extraction quality, EICAR, corrupt ZIPs, excessive DOCX entry/uncompressed size, and archive path traversal.
- Recommendation and artifact validators reject unknown evidence, unsupported official requirements, scientific invariant loss, cross-format proposal mismatch, secrets, and private storage paths.
- Project deletion now removes uploads, private analyses, decisions, and all generated artifacts. Shared journal knowledge remains only as source-backed derived profile data.
- DOCX export clears creator/last-modifier values, revision session identifiers, and custom properties while retaining supported document parts.
- Repository secret scanning, production npm audit, container smoke tests, and Grype image scans are release gates. CodeQL analysis is configured in CI.

## Scan result and residual risk

No critical/high fixed vulnerabilities were reported by the production npm audit or fixed-image Grype gate. Current base runtimes reported medium/low findings. Python findings shown by Grype had fixes only in Python 3.15 prereleases; Node findings require a future supported runtime-line upgrade. These findings do not meet the frozen critical/high blocking threshold, but remain tracked and must be rescanned before deployment.

The local pilot still uses a shared invitation token, SQLite/local objects, synchronous work, and an EICAR-pattern placeholder rather than a production malware engine. Those constraints prohibit uncontrolled production use and are addressed by the Change 006 deployment design.
