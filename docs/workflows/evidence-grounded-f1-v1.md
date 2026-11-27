# Evidence-Grounded F1 v1

Projection identifier `evidence_grounded_f1_v1`. The projection reads verified
Evaluation Protocol v1 Condition results and leaves their Graph and proof
counts intact. It uses the protocol's semantic edges and attached Sufficient
Evidence Alternatives.

| Outcome | Graph | Evidence-Grounded |
| --- | --- | --- |
| Correct edge with a complete alternative | TP | TP |
| Correct edge without a complete alternative | TP | FP and FN |
| Missing expected edge | FN | FN |
| Unsupported prediction | FP | FP |

An alternative is complete when the same canonical relationship carries every
required exact (Source ID, approved quotation) pair. Construction pools
evidence on a single canonical edge. The evaluator counts the semantic edge
once even if several alternatives are complete. Ordinary provenance and Source
attribution are separate diagnostics with different approval sets. Each member
of a complete formal route already passes exact attribution to its specified
Source under the formal proof contract.

Grounded TP equals the sum of the protocol's complete proofs. The historical
protocol annotates critical relationships, a subset of expected relationships.
A correct edge without a formal alternative cannot earn grounded TP under
this metric. It remains a Graph TP and contributes one grounded FP and FN.
This includes v3's 113 expected edges and 71 formal proof targets. The
denominator of grounded recall is all expected relationships in observed
qualified Conditions. Complete Proof Rate uses only formal proof targets.
They agree when denominators coincide and the numerator is shared.

Pool counts across Conditions before computing precision, recall and F1.
For each Condition let G be graph counts and C its complete proof count.
Grounded counts are (C, G.fp + G.tp - C, G.fn + G.tp - C). The prediction
and reference denominators stay the same as for same-scope Graph F1, so
Evidence-Grounded F1 cannot exceed it. A zero denominator yields 0. A proof
rate with no formal targets is unavailable.

Benchmark v4 combines 35 inputs under mixed references for Graph F1.
Grounded metrics cover the 34 originally qualified Conditions. U revision 8
contributes to combined Graph F1 and retains its separate citation-overlap
diagnostic. It has no exhaustive formal proof contract.

The projection includes retained terminal observations. Failed construction,
provider or parsing failures, and uncertain attempts without a retained graph
produce all expected edges as FN, retaining their separate outcome labels.
A valid empty graph remains a successful construction with zero predicted
edges. Unexecuted and currently processing slots contribute no counts to the
observed projection. Coverage is explicit and an unfinished Run is provisional.
The original protocol's planned-input Graph F1 remains available as a historical
result. Its provisional denominator includes unobserved slots.

The CLI and Workbench derive this projection after existing Run, scorer,
reference, receipt and candidate-lineage verification. No original artifact,
frozen scorer file or provider accounting changes are needed.

The first live v3 baseline replays to grounded counts 18 TP, 83 FP and
95 FN, micro-F1 16.82%, and grounded recall 18/113 (15.93%). Complete Proof
Rate is 18/71 (25.35%) and Joint-only Proof Rate is 0/30. To regenerate the
baseline JSON without writing into its archive:

```sh
uv run python -m private_client_graph.research inspect-v3-baseline ARCHIVE_DIRECTORY ADMISSIONS.json
```
