# Six-axis diagnostic benchmark

The twelve synthetic fixtures under `benchmark_v1/` complement Cases 01–05 and
the ten published evaluation cases. Each axis has one development fixture and one
designated held-out fixture. They exercise exhaustive reconstruction of the current
Person/Trust graph from ordered Sources.

| Axis | What to inspect in the complete graph |
| --- | --- |
| Aliases | Explicitly linked surface names resolve to the source-supported participant. |
| Authority | Current roles follow the particular instruments and intentions described in the fictional matter. |
| Cross-source | Facts across both Sources survive with the correct supporting Source. |
| Distractors | Additional names and unsupported roles introduce no current relationship. |
| Drafts and proposals | Asserted family facts survive, including those embedded in proposed appointments. |
| Temporal | An effective replacement removes the former trustee and preserves unchanged earlier facts. |

## Execution and selection

The current pipeline can attempt all six tasks. It supplies the entire ordered
Source bundle to one extraction call, optionally resolves endpoint names, then
constructs a validated current graph. The fixtures ask for a final snapshot.
Representing unresolved conflicts or a history of states would require a separate
contract decision. Ground truth, ideal extractions and approvals belong to
evaluation and are excluded from operational model input.

In the Research Workbench, create an Experiment, open **Choose cases**, clear the
selection and select the six **Development** entries. Choose **Saved replay · No
provider calls**, **Saved extraction snapshots** and **No resolution**. Freeze
the Run, review the planned six observations, then start it. Open **Observations
& Evidence** to inspect results and follow predicted and expected quotations to
their original Sources. The Run retains inputs, metadata, hashes, results and
coverage. The five historical default inputs keep their previous selection.
Both the development diagnostics and designated held-out fixtures require an
explicit selection. Reserve the latter for isolated annotation QA or a separately
approved evaluation on a frozen pipeline.

Each case's metadata records its stable ID, axis, split and matter family. The
Workbench fixture ID appends `_fixture`. A package contains the complete
`ground_truth.json`, ordered `sources.json`, Source/quote approvals in
`source_evidence.json`, and an attributed ideal in
`expected_source_extraction.json`. The combined `source.txt` and corresponding
`expected_extraction.json` retain the legacy representation. A one-Source
manifest may reference `source.txt` directly. Follow the existing Case 04/05
conventions and the two-direction authoring audit before deriving either ideal.
[Authoring workflow](synthetic-case-authoring.md)

## Reproducing the checks

From the repository root, exercise the catalogue, deterministic pipeline,
persisted Run, aggregate and Evidence inspection with:

```sh
uv run --locked pytest tests/workbench/test_benchmark_v1.py tests/research/test_source_attribution.py
```

To reproduce a committed legacy graph/quotation score independently, use a new
destination. The helper refuses an existing output and accepts legacy candidates.
The Workbench replay above exercises Source attribution.

```sh
case_dir=benchmark_v1/authority/dev/case_1
result_dir=$(mktemp -d)
uv run --locked python benchmark_v1/evaluate_case.py "$case_dir" \
  "$case_dir/expected_extraction.json" --output "$result_dir/score.json"
```

## What the Run measures

| Measure | Contract |
| --- | --- |
| Graph counts | TP, FP and FN count distinct exact-name, typed edges. Direction matters for parent and trust roles. Spouse and sibling are symmetric. |
| Precision, recall, F1 | TP/(TP+FP), TP/(TP+FN), and 2TP/(2TP+FP+FN). A scored zero denominator yields 0.0. Run micro F1 pools edge counts over scored observations. True negatives are unspecified, so report the FP count. |
| Approved-quotation accuracy | TP edges with at least one attached exact approved quote divided by all TP edges. With zero TPs the scorer returns 0.0. Alternative quotes may each suffice. Semantic support requires annotation review. |
| Source attribution | Approved attached (Source ID, exact quotation) associations on TP edges divided by all assessed associations on TP edges. One edge can contribute several associations. Zero assessed yields an unavailable ratio. A quote occurring in two Sources can pass the quotation check and fail the Source check. |
| Coverage | Report scored/planned observations and counts of failed, uncertain, pending and unavailable slots. Only scored observations contribute edges. No scored observations means unavailable Run F1. Partial coverage yields provisional quality. |

Authored ideal replay establishes internal agreement and exercises mechanical
validation. Live model quality, variability and resource costs require separately
authorised experiments. The existing published A/A′/B study has its own frozen
input scope, scores and replay provenance. [Publication workflow](public-research-publication.md)

## Split limitations and next decisions

At initial review all six dev/held-out pairs shared their directed typed graph
structure under entity ordering. The temporal dev case also shares its named
answer graph with Case 05. Several axes mix difficulties, particularly authority
with recency and explicit effectiveness. The two splits are useful for controlled
inspection. Independent generalisation would require separately authored matter
families kept wholly within split, including composites and positive/negative
controls. Record lineage and revisions before any independent final freeze.

All six designated held-out fixtures received isolated semantic annotation QA.
The prior reviewer reported aggregate defects, followed by the correction pass
documented below. No held-out model results guided changes. [Held-out audit and revision digests](../../benchmark_v1/held-out-audit.md)

Future work starts with observed development errors. A retrieval comparison would
use the same original matters, full context versus selected context, matched
downstream processing and separate evidence-sufficiency diagnostics. Its
specification, budget and execution require separate decisions. Document count
alone does not establish context pressure. Question answering would introduce a
different product task and its own evaluation.
