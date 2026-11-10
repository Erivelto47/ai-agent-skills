# Private sources for the example handoff

Not shared. This companion file keeps what the shareable handoff must not carry: where the recording and the normalizer output live, and which evidence supports each section. Mark it as private and keep it out of version control in real use.

- Normalizer output directory: `<outputs.root>/<sha256-prefix>-<source-stem>/` (for a real meeting, the absolute path on the owner's machine).
- Recording: held by the owner only; not available to the reader.

| Handoff section | Supporting evidence | Notes |
|---|---|---|
| 2. Export architecture | `evidence.json` claims `c-014`, `c-015`; segments 212-230 | The choice was never stated as a formal decision; see "How the choice appeared" |
| 3. Contradiction on the status endpoint | `uncertainties.json` entry `u-007`; segments 41 and 388 | The later statement is more specific |
| 5. Actions | `evidence.json` actions `a-002`, `a-003`, `a-004` | All are `action_mentioned_in_meeting` |

Names confirmed by the user in chat (not by the evidence): none in this example.
