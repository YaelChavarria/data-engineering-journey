# Security and Privacy

This repository contains no real client data. All records are deterministic synthetic examples and all local outputs are ignored by Git.

## Production controls represented by the blueprint

- Least-privilege access to source and delivery locations
- Separate storage and credentials per client
- Secrets kept outside the repository
- PII inventory and minimization before transformation
- Encryption in transit and at rest
- Access and delivery audit logs
- Retention and deletion rules agreed in the engagement
- Approval path for new users and new data sources

## Delivery boundary

The partner should receive only the fields needed for the agreed decisions. Raw exports should not be copied into personal devices or public repositories. A real engagement would require a data-processing agreement, access review and incident-notification terms before ingestion.

## Portfolio limitation

The local demonstration shows process and quality evidence, not a security certification. Cloud IAM, secret rotation, network controls and compliance requirements remain deployment work.
