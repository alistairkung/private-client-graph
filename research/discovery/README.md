# Alder Trust Source discovery evaluation

On this synthetic corpus, the original search surfaced the deed and resignation email. Approving the appointment lead added the third relevant Source. Approving the earlier signed-notice lead added one irrelevant email. The ranking switched from Mara Voss to Ben Wong when the promise in the sixth message changed, even though both versions named the same five people.

Run from the checkout with `uv run python -m research.discovery.evaluate`. It prints deterministic JSON with each checkpoint and approval. Add `--timing` for elapsed offline milliseconds per arm. Run `uv run pytest tests/discovery/test_evaluation.py` for the matched-checkpoint, approval replay, one-hop and resource-limit controls.

## What counts

The discovery question is which Sources document the original trust and the trustee change. The [item labels](labels.json) identify three relevant objects, eight irrelevant eligible objects and three exclusions. Labels use provider kind and fixture ID. Relevance follows the fictional role of the documents in the corpus. The shared PDF byte fixture tests acquisition and does not establish substantive legal relevance. The scorer loads labels only after both variants and arms have run. The client, ranker and scripted practitioner do not receive them.

Recall is relevant items surfaced / all three relevant eligible items. Precision is relevant items surfaced / all distinct eligible items surfaced so far. A listed PDF counts before download. A returned eligible email counts before inspection. The evaluation excludes the unlabelled sibling, out-of-folder PDF and shortcut. An unknown or excluded candidate fails scoring. An empty denominator yields JSON null. An executed lead is false here if its completed search returns zero relevant eligible items. A partial search with no relevant hit yet is indeterminate. Irrelevant hits count individually, including on otherwise successful searches.

## Matched replays

Both arms start a new DiscoverySession with the same Alder Trust v1 fixture, `Alder Trust` query, `alder-label`, direct parent `folder-1` and no dates. The JSON records the corpus SHA-256. Run at the report’s Git revision to reproduce the HTTP pages and ranker. Each original batch admits up to five new items, capped at 50. Sorted message IDs within each page give 01–05 first and 06 next. The original Drive listing finishes on the third batch. Both arms use 40 requests / 12 MiB per action and 160 requests / 32 MiB per discovery session. Access to additional original pages is reported at each checkpoint.

The expanded arm approves the highest-ranked suggestion after the first batch, opens its first returned email, completes the original batches, then approves the current top suggestion. Those two decision points are fixed before scoring. The rule ranks promised appointments ahead of other promised documents, breaks ties by name and origin, and keeps up to three distinct suggestions from inspected originals. Every approval records its revision, ordered shortlist with passage, rationale and origin, original inspected IDs and body hashes, query, returned IDs and pre-search usage. The Gmail fixture has no provider revision field. Each message ID and SHA-256 of its exact inspected text identifies the content version used for ranking. The corpus digest pins the accompanying fixture metadata.

| Primary checkpoint | Original recall | Original precision | Expanded recall | Expanded precision | Expanded requests / response bytes (cumulative) |
| --- | --- | --- | --- | --- | --- |
| Five original emails inspected | 0/3 | 0/5 | 0/3 | 0/5 | 11 / 3,109 |
| Same five, signed-notice lead approved and dispatch opened | 0/3 | 0/5 | 0/3 | 0/6 | 15 / 3,790 |
| Sixth email inspected, deed listed | 2/3 | 2/7 | 2/3 | 2/8 | 20 / 5,309 |
| Original pages complete, parking minutes listed | 2/3 | 2/8 | 2/3 | 2/9 | 21 / 5,477 |
| Same six, appointment lead approved | 2/3 | 2/8 | 3/3 | 3/10 | 23 / 5,807 |

The original-only replay used 17 requests and 4,796 response bytes. Expansion and the scripted email open added six requests and 1,011 bytes. The primary expanded arm had one false lead in two approvals and seven irrelevant hits among ten distinct eligible results. Its last approval alone cost two requests and 330 bytes.

The paired control changes the actor in the promise and the filing name on the appointment. Ben's search also returns a pre-existing irrelevant dispatch. Original-only finished at 2/3 recall and 2/8 precision (17 requests, 4,792 bytes). Expansion reached 3/3 and 3/11 (23 requests, 5,813 bytes). In each expanded arm the out-of-label sibling was skipped, zero original emails failed or remained pending, and no budgets were exhausted. The paired arm left the additional dispatch unread. Listed PDFs were never inspected in either arm. The tests also exercise a one-request session with five pending emails and unenumerated pages, as well as a repeated approval click and the actionable promise inside the opened follow-up email.

## Effort and timing

Each scripted practitioner started one search. The original-only arm made zero individual opens, approvals or selections. The expanded arm made one individual open, two approval clicks and zero selections. Original continuation was automatic. Selection and import are beyond the discovery endpoint measured here. No model calls, tokens or provider charges were incurred.

One local offline run measured 2.03 ms original-only and 1.81 ms expanded for the primary fixture, and 1.30 ms and 1.74 ms respectively for the pair. These single-run timings include in-process HTTP replay and session work. No human walkthrough was timed. They provide no estimate of practitioner time or Google network latency.

The live pilot observed a different within-page ordering of Google IDs, which placed the resignation in the first inspected batch. Its scope and acquisition observations are recorded in the [pilot runbook](../../docs/workflows/workspace-pilot.md). The matched sixth-message gain above applies to the pinned offline pages. The pair exercises sensitivity to the actor in one promise and cannot estimate recall in other matters.
