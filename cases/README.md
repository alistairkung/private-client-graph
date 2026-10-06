# Evaluation Cases

## Benchmark hypothesis

Can the system reconstruct family/trust relationship graphs from
realistic synthetic private-client source material while preserving
valid provenance?

## What the benchmark varies

Cases should increase difficulty deliberately rather than simply
becoming larger.

Candidate dimensions include:

- graph complexity;
- linguistic ambiguity;
- relationship density;
- entity ambiguity;
- source-document genre;
- distractor information;
- provenance ambiguity;
- repeated or overlapping evidence;
- conflicting / superseding information;
- cross-document reconciliation.

Not every case should vary every dimension.

Prefer cases that isolate a small number of meaningful challenges so
failures remain diagnosable.

## Case progression

| Case | Primary hypothesis | New difficulty | Held relatively stable |
|------|--------------------|----------------|------------------------|
| 01 | Can the baseline pipeline recover explicit family/trust facts with provenance? | Baseline | — |
| 02 | Can it decompose denser family information while keeping family and trust roles distinct? | multi-edge statements, sibling relationship, role overlap, richer provenance choices | explicit/cooperative language |
| 03 | Can it resolve the same person referred to by multiple surface forms without splitting or merging entities incorrectly? | entity aliases (informal names, role references, surname variants) | explicit/cooperative language, single document |
| 04 | Can it reconcile the same relationship asserted across more than one source document, attaching provenance to the correct document? | cross-document extraction and provenance | explicit language, no aliases |
| 05 | Can it distinguish a currently-true relationship from one that has changed, without confusing the two? | temporal state (a trustee replaced, or a spouse described as former) | explicit language, single difficulty per case |
| 06 | Can it surface a genuine contradiction between sources rather than silently picking one? | conflicting evidence | explicit language, temporal order stable |
| 07 | Can it handle a person whose family role and trust role could be conflated, where the source deliberately does not distinguish them? | ambiguous role attribution | aliases and multi-doc stable |
| 08 | Can it recover relationships expressed only through indirect description rather than explicit assertion? | indirect / inferential language | vocabulary fixed, no contradictions |
| 09 | Can it avoid extracting relationships from hypothetical, proposed, or negated statements? | negation and hypotheticals | explicit positive statements stable |
| 10 | Can it handle a larger family graph without degradation in precision or recall? | graph size and density | single trust, explicit language |
| 11 | Can it handle multiple trusts in one source without misattributing roles between them? | multiple trust entities | single family, explicit language |
| 12 | Can it handle a corporate or non-person trustee? | entity-type extension (organisation as trustee) | single trust, explicit language |
| 13 | Can it handle a source in a different document genre (letter, file note, deed recital) without loss of accuracy? | document genre shift | difficulty held at Case 01-02 level |
| 14 | Can it handle relationships split across sentences with locally-resolvable pronouns only? | pronoun resolution under distance | explicit names nearby |
| 15 | Can it distinguish sibling relationships from cousin relationships where both appear? | relationship-type confusability | vocabulary fixed |
| 16 | Can it handle source material where the same fact appears in multiple overlapping spans? | overlapping provenance | single document, explicit language |
| 17 | Can it recover relationships when the source is longer and contains substantial irrelevant material? | distractor density and length | single difficulty |
| 18 | Can it handle partial information — a relationship asserted but a participant unnamed, requiring the correct behaviour (which may be to omit, not guess)? | incomplete information | explicit language elsewhere |
| 19 | Can it handle a source that describes historical relationships (former spouse, deceased settlor) without treating them as current? | historical vs current state | temporal from Case 05 understood |
| 20 | Composite stress test — deliberately combines several earlier difficulties at once. | composite | nothing held stable |

## Notes on Case 02

Case 02 is a deliberately **composite** case: it introduces several new
difficulties at once, rather than the single new difficulty preferred for
later cases. This is intentional and follows the stated design for this
case (multi-edge statements, sibling relationship, role overlap, richer
provenance choices).

"Role overlap" is interpreted here as **one person holding multiple
roles** — specifically, Henry Lau is spouse, parent, and trustee. This
interpretation should be confirmed. If "role overlap" was intended to mean
something else (for example co-trustees, or two roles asserted in one
sentence), the case should be revised accordingly.

Case 02 introduces two relationship types not exercised in Case 01:
`sibling_of` and `trustee_of`. Between them, Cases 01 and 02 exercise the
full current vocabulary of six relationship types.