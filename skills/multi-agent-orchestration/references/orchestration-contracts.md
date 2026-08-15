# Orchestration contracts

Use these contracts to keep delegated work bounded and auditable.

## Capability map

| Front | Capability needed | Adapter/provider selected | Availability checked | Owner |
|---|---|---|---|---|
| Discovery | Search and symbol navigation | Local adapter | Yes or no | Role or agent |

Use capability names in the public plan. Keep concrete provider, model, credential, and path details in a private adapter.

## Child task envelope

```text
Task ID:
Role:
Closed objective:
Allowed scope:
Ownership:
Context minimum:
Capabilities and tools:
Verifier:
Acceptance criteria:
Escalation condition:
Stop conditions:
Return contract:
```

The child task must be complete without reopening unrelated history. Never assign overlapping writable paths to multiple workers.

## Worker return contract

```text
Status: COMPLETE | PARTIAL | BLOCKED | FAILED
Objective:
Observed facts:
Changed paths:
Commands and results:
Artifacts or evidence paths:
Unverified assumptions:
Blockers:
Recommended next step:
```

## Validation report

```text
Checks executed:
Results:
Failures or skips:
Artifacts and log paths:
Unverified assumptions:
Final confidence:
Gate status: PASS | PARTIAL | BLOCKED | FAIL
```

## Dispatch rules

- Dispatch only after scope, ownership, verifier, and acceptance criteria are explicit.
- Pass the minimum context required for the task.
- Prefer deterministic tools for search, builds, tests, and state inspection.
- Use an independent reviewer when risk or ambiguity justifies it.
- Escalate unavailable capabilities, conflicting evidence, unsafe operations, and human decisions.
