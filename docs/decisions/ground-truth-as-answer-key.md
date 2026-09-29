# Ground truth as the Case 01 answer key

## Decision

For this project, `ground_truth.json` is best understood as the **answer key for the graph-extraction task**, not as an exhaustive database of every true fact in the fictional world.

For Case 01, the extractor is being asked to identify:

- people;
- trusts;
- relationships using the six currently supported relationship types:
  - `parent_of`;
  - `sibling_of`;
  - `spouse_of`;
  - `settlor_of`;
  - `trustee_of`;
  - `beneficiary_of`.

The ground-truth fixture must contain every correct relationship of those kinds that exists in the synthetic case.

## Why this distinction matters

A realistic attendance note can contain many true facts that are not relationship-graph facts.

For example:

- the meeting lasted approximately one hour;
- the meeting was an initial fact-finding/review meeting;
- Alice wanted the factual position checked before further review;
- substantive advice would follow later;
- a follow-up was agreed.

Those facts can safely exist in the fictional scenario and in `source.txt` without being added to `ground_truth.json`, because the extractor has not been asked to reconstruct them.

This lets the source document contain realistic professional context without forcing the graph model to represent every proposition in the document.

## Evaluation consequence

Precision and recall are meaningful only if the ground truth is complete **for the task we have actually asked the extractor to perform**.

If the source contains a true `parent_of`, `spouse_of`, `beneficiary_of`, etc. relationship that is missing from `ground_truth.json`, the evaluator could incorrectly treat a correct extraction as a false positive.

Therefore:

> Every true relationship in the source that fits the supported Case 01 relationship types must appear in the ground-truth answer key.

Conversely, a true fact such as meeting duration is not a missing ground-truth relationship because meeting duration is outside the extraction task.

## Implication for synthetic source generation

We can make `source.txt` substantially more realistic by adding graph-neutral discussion such as:

- meeting purpose;
- Alice's objectives;
- questions and answers;
- explanations of the review process;
- clarification and repetition;
- recap;
- procedural next steps.

However, fixture authors must be careful not to accidentally introduce additional facts that fit one of the supported graph relationship types.

For example, casually mentioning another child, sibling, spouse, beneficiary, settlor, or trustee would change the correct answer key and would therefore require a corresponding change to `ground_truth.json`.

The practical rule is:

> Add realistic context freely when it is outside the graph task, but treat every statement that creates a supported family/trust relationship as a deliberate change to the benchmark answer key.

## Case 01

The current Case 01 answer key remains unchanged:

- Alice Chen is settlor of the Evergreen Family Trust.
- Alice Chen and David Chen are spouses.
- Alice Chen is a parent of Bob Chen.
- David Chen is a parent of Bob Chen.
- Bob Chen is a beneficiary of the Evergreen Family Trust.
- Carol Wong is a beneficiary of the Evergreen Family Trust.

The longer attendance note should add realistic meeting context around these facts without creating any additional supported graph relationships.
