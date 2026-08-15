# Implementation checklist

Use this checklist to turn a validated discovery into a handoff-ready change.

## Change definition

- [ ] Desired outcome and acceptance criteria are explicit.
- [ ] Allowed and excluded scope are explicit.
- [ ] Expected changed paths and ownership are listed.
- [ ] Compatibility, security, data, and rollout risks are considered.

## Implementation

- [ ] Project instructions and current worktree state were read.
- [ ] The change follows existing conventions.
- [ ] Unrelated cleanup was avoided.
- [ ] Secrets, private identifiers, and environment-specific details are absent.
- [ ] Public contracts changed only when explicitly required.

## Validation

- [ ] Focused tests or checks were run.
- [ ] Broader checks were run when risk justified them.
- [ ] Failures and skips are recorded accurately.
- [ ] The diff was inspected for accidental scope expansion.
- [ ] Remaining uncertainty and unverified behavior are stated.

## Handoff

Return status, changed paths, commands, results, artifacts, risks, and the next requested decision. Do not imply commit, merge, release, or deployment unless it happened and was authorized.
