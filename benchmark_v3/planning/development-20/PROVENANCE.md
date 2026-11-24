# Planning provenance and boundaries

## Reviewed revisions

The planning branch starts at the passing #197 revision, which includes the permanent Research Architect, the updated admissions and the resumable batch factory. The pilot is a sibling branch. Its public proposed portfolio supplies reservation metadata only.

| PR | Remote head checked | Role |
| --- | --- | --- |
| [#193](https://github.com/alistairkung/private-client-graph/pull/193) | `1921b4e90e832993c77f5532a0fd3e5df9b6fd25` | Original factory and Family A admission |
| [#194](https://github.com/alistairkung/private-client-graph/pull/194) | `ed9b9a4df37ada85f7defac440a4d06154b2ed72` | Families B and C |
| [#195](https://github.com/alistairkung/private-client-graph/pull/195) | `3641948e8f8510b15799b96d1b748825d0048645` | Permanent Research Architect |
| [#196](https://github.com/alistairkung/private-client-graph/pull/196) | `d6a1edbc86d93ce75f492ccd82be519e027a247f` | D/F admissions and E return |
| [#197](https://github.com/alistairkung/private-client-graph/pull/197) | `550b246b51bd93e2bb5d8dc96ceb773305ea0375` | Isolated planning base and resumable factory |
| [#198](https://github.com/alistairkung/private-client-graph/pull/198) | `994cc5c03e37def46d710df922307b529e3ca427` | Separate public H/I/J reservations |

Admitted technical findings came from the canonical coverage and owner record. The public H/I/J portfolio at #198 has Git blob ID `1a90baccdcf863bd022b17ded12959d5fd16b762`. Intake used its scope, axes, intended workload, condition counts and revision commitments. No pilot design, private history, receipt, ledger, private approval, extraction result or release status was inspected. No sealed v3 evaluation material or custody path was opened.

## Runtime boundary

The stock packet runner binds the exact input and prompt digests, profile and response in each handoff. The named `benchmark_packet` profile uses an empty ephemeral workspace, denied network, denied user and shared temporary paths, no active connectors and no tool actions. The custodian checked a harmless allowed sentinel and two denied probes using the same profile and CLI, without inference. [Filesystem evidence](os-boundary.json) · [Packet verifier](../../architect.py)

## Session accounting

| Packet | Charged Architect turn | Outcome |
| --- | ---: | --- |
| [App-server startup](packets/startup-failure/receipt.json) | 0 | The outer sandbox blocked process startup before a Codex thread or turn was confirmed. The receipt lacks isolation and submission metadata. |
| [First submitted planning turn](packets/schema-rejection/receipt.json) | 1 | The response selected hypothesis schema v1 for a one-condition proposal and failed validation. |
| [Second submitted planning turn](packets/shape-rejection/receipt.json) | 1 | The response serialized required list fields as text and failed validation. |
| [Independent critique and selection](packets/planning/receipt.json) | 1 | GPT-6.2 Sol High independently reviewed a schema-validated custodian draft. The turn finished, and its packet was rejected for a malformed copy of a supplied reference URL. |

The startup attempt is separate from the three actual Architect session attempts. The first two submitted responses did not enter the planning register. For the final turn, a custodian-only wrapper around the stock turn handler retained the returned response before post-turn schema validation. It left the actual runner, isolation, inputs and validation outcome unchanged.

The [original captured response](packets/planning/output-captured.txt) has one malformed copy of the staged GRO URL in Family L. The [custodian validation](packets/planning/custodian-validation.json) commits the exact rejected runner receipt, original handoff, raw response, corrected response and normalized planning record. It records a single URL replacement with the exact staged URL. The stock result validator accepts those corrected bytes against the original allowlist. The planned lineages bind the original model output digest and the validated recovered content. The stock completed-packet verifier correctly rejects the original receipt. A completed Architect packet receipt remains unavailable within this task's three-session allowance.

The factory-compatible portfolio was projected from the repaired planning result. The stock portfolio validator independently checked the exact hypothesis references and admitted coverage. The work has no separate portfolio-profile turn. [Reproduction and checks](VALIDATION.md)

**Usage** · Three Architect turns attempted out of three. Zero Matter Designer, Document Author, Blind Annotator or Adjudicator sessions. Zero paid PCG extraction calls. No commissioning, baseline execution, automated approval, or admission record mutation.
