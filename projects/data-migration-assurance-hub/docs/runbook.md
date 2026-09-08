# Cutover Runbook

## Source intake failure

1. Confirm the migration ID and wave.
2. Check that all source and target files arrived.
3. Review the quality report for null keys, duplicates or orphan records.
4. Notify the data owner with the failed check and sample records.
5. Do not build or publish a cutover decision from an invalid source.

## Reconciliation difference

1. Open the exception queue for the entity and record key.
2. Assign the issue to the source, Finance, CRM or Data owner.
3. Compare the legacy record, mapping rule and target record.
4. Record the resolution or approved exclusion.
5. Re-run the migration review and preserve the new manifest.

## HOLD decision

1. Communicate the decision and blocking reason.
2. Confirm that Finance and the Business owner received the evidence.
3. Keep the wave in review; do not mark it ready through a manual override.
4. Resolve high-severity exceptions or obtain a documented client-approved exception.
5. Re-run reconciliation before cutover.

## Recovery

The demonstration is deterministic and can be replayed from the source and target snapshot directories. A production implementation would preserve immutable snapshots, isolate each wave and support rollback to the last accepted target state.
