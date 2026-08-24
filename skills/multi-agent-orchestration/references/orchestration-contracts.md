# Orchestration contracts

Use these contracts to keep delegated work bounded and auditable.

## Capability map

| Front | Capability needed | Execution surface | Provider/executor | Availability and budget checked | Owner |
|---|---|---|---|---|---|
| Discovery | Search and symbol navigation | Delegated agent | Local adapter selection | Yes or no | Role or agent |

Use capability and surface classes in the public plan. Resolve concrete providers, models, effort levels, commands, credentials, and private paths through the active environment or local adapter.

## Resource ledger

```text
Executor/provider:
Available: yes | no | unknown
Capabilities and tools:
Supported task surfaces:
Model or quality tiers:
Supported reasoning or compute range:
Context and isolation:
Concurrency limit:
Budget/quota state: healthy | constrained | reserve | exhausted | unknown
Reset horizon or cost signal:
Evidence and timestamp:
```

Do not probe an executor wastefully merely to fill the ledger. Use available configuration, capability metadata, or a cheap adapter-defined preflight. Preserve uncertainty when exact quota is not observable.

## Child task envelope

```text
Task ID:
Role:
Closed objective:
Dependencies:
State/revision:
Allowed scope:
Out of scope:
Ownership:
Execution surface:
Resolved provider/executor:
Resolved model/quality tier and reasoning/compute:
Availability and budget evidence:
Context strategy and context packet:
Capabilities and tools:
Isolation and permission mode:
Time, retry, and token/cost bounds:
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
Executor/provider actually used:
Model/quality tier and reasoning/compute actually used:
Budget, timeout, or fallback events:
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
- Verify the concrete executor, model or quality tier, reasoning or compute setting, permissions, and task surface before dispatch.
- Respect dependency, concurrency, context, and quota constraints; reserve capable capacity for synthesis and recovery.
- A coordinator may use a different provider for implementation or review when the task envelope and verifier remain authoritative.
- Use an independent reviewer when risk or ambiguity justifies it.
- Escalate unavailable capabilities, conflicting evidence, unsafe operations, and human decisions.
