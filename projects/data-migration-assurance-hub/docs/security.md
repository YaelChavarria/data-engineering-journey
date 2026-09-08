# Security and Privacy

This repository uses synthetic records only. No client credentials, personal data or production extracts are stored.

## Controls expected in production

- Separate access boundaries for each client and migration wave
- Least-privilege read access to source systems
- Encrypted transport and storage
- Secrets management outside code and repositories
- Field-level classification for personal and financial data
- Audit logs for snapshot intake, transformation and sign-off
- Retention and deletion rules agreed before the migration
- Formal data-processing and confidentiality agreements

## Data handling boundary

The data partner should receive only the fields needed to reconcile and migrate the agreed entities. Raw snapshots should remain in governed storage and should never be copied into a public repository.

The dashboard displays evidence for a synthetic demo. It is not a security certification or a substitute for a client security review.
