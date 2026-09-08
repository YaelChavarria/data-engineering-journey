# Delivery Plan

## Phase 1: Discover

- Confirm source systems, target model and migration wave.
- Inventory entities, keys, financial fields and data owners.
- Agree on reconciliation tolerances and severity rules.
- Define go/no-go criteria and sign-off roles.

**Output:** migration brief, source inventory and reconciliation contract.

## Phase 2: Profile and map

- Profile nulls, duplicates, domains and referential relationships.
- Map legacy fields to target fields.
- Identify transformations and known exclusions.
- Define quarantine and exception handling.

**Output:** mapping specification, data contract and quality baseline.

## Phase 3: Migrate and reconcile

- Receive source and target snapshots for the wave.
- Run source quality gates.
- Compare counts, keys, amounts and critical attributes.
- Generate the exception queue and owner assignments.

**Output:** reconciliation report and issue queue.

## Phase 4: Cutover review

- Review high-severity exceptions with the responsible owners.
- Confirm Finance and Business sign-off.
- Record `READY` or `HOLD` in the migration manifest.
- Preserve evidence for the project record.

**Output:** cutover decision, checklist and client acceptance package.

## Responsibilities

| Workstream | Data partner | Client |
|---|---|---|
| Reconciliation design | Lead | Approve |
| Source access and definitions | Support | Own |
| Transformation and controls | Own | Review |
| Financial validation | Facilitate | Approve |
| Exception resolution | Track | Own source/business fix |
| Cutover decision | Recommend | Approve |
