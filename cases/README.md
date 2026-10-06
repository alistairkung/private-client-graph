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
| 03 | TBD | TBD | TBD |

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