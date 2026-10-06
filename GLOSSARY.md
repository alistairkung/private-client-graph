# Private Client Graph

Private Client Graph reconstructs reviewable family and trust relationships from source documents while preserving the evidence for each relationship.

## Language

**Benchmark Case**:
A synthetic source document, complete relationship answer key, and associated fixtures used to exercise and evaluate the pipeline under controlled conditions.
_Avoid_: Client case, production case

**Relationship Candidate**:
A raw semantic claim extracted from source evidence, consisting of two named endpoints, a supported relationship type, and exact supporting text. It has not yet passed deterministic graph construction.
_Avoid_: Edge, canonical relationship

**Canonical Graph**:
The deterministic, mechanically validated representation of entities, relationships, and first-class evidence produced from relationship candidates. Its placement supplies its product meaning: a Matter Proposal holds a machine-proposed graph, while a Matter holds the professionally accepted current graph.
_Avoid_: Raw extraction, model output

**Evidence**:
An exact supporting quote attributable to one Source, potentially supporting multiple Relationships. Evidence is distinguished by its Source and exact text: repeated identical quotes within one Source are one Evidence item, identical quotes from different Sources are distinct, and no particular occurrence within the Source is implied.
_Avoid_: Justification, rationale

**Entity**:
A Person or Trust identified within one Matter's relationship state. Its name describes it but does not define its identity; matching names alone do not establish that two Entities are the same participant.
_Avoid_: Name string, globally identified person

**Professional Review**:
Inspection by a private-client professional of AI-extracted relationships and the source evidence supporting them. It is distinct from benchmark evaluation; the existing Matter workspace is read-only, while Matter Intake requires whole-proposal confirmation without yet supporting human correction.
_Avoid_: Case summary, benchmark review

**Live Analysis**:
An analysis that obtains relationship candidates from a new model invocation before deterministic graph construction.
_Avoid_: Replay, sample analysis

**Sample Analysis**:
A deterministic demonstration path that loads the Case 01 ideal-extraction fixture and passes it through current graph construction. It is explicitly selected and is never a fallback from live analysis.
_Avoid_: Live analysis, prior-run replay

**Run Artifact**:
A persisted raw extraction created for reproducibility and diagnosis. It is technical traceability data, not application state or a professional case history.
_Avoid_: Saved case, analysis history

**Benchmark Evaluation**:
Offline comparison of a canonical graph with a benchmark case's known answer key, including relationship and provenance metrics. It is separate from professional review.
_Avoid_: Professional review score, confidence score

**Matter**:
A scoped piece of professional work through which a practitioner accesses the authoritative source and professionally accepted current relationship graph relevant to that work.
_Avoid_: Case, client record, trust record

**External Matter Reference**:
A practitioner-facing identifier assigned by a firm's existing matter-management ecosystem. Private Client Graph stores it as display and integration metadata but does not generate or govern it.
_Avoid_: Case ID, generated Matter reference

**Authoritative Source**:
An explicitly identified body of source text treated as authoritative for a Matter's current relationship graph, also called a Source. Separately designated Sources within a Matter remain distinct even when their titles and text match; an acquisition file is not itself the Authoritative Source, and distinct Sources do not necessarily constitute independent corroboration.
_Avoid_: Benchmark fixture, uploaded document

**Public Showcase**:
The explicitly synthetic demonstration journey that exposes live or sample analysis of fixed Case 01 material. It is separate from the persisted practitioner application.
_Avoid_: Matter workspace, practitioner application

**Practitioner Application**:
The Matter-oriented application journey used to identify and open durable professional review state. It does not expose showcase analysis controls or benchmark terminology.
_Avoid_: Public showcase, benchmark dashboard

**Matter Intake**:
The practitioner workflow that supplies externally governed Matter identity and source material, produces structured relationship proposals for Professional Review, and creates a complete Matter after explicit whole-proposal confirmation.
_Avoid_: Matter import, document upload

**Matter Proposal**:
Durable pre-Matter review state created after successful synchronous analysis, containing proposed Matter identity, an Authoritative Source, and a proposed Canonical Graph awaiting practitioner confirmation or discard.
_Avoid_: Intake job, proposed Matter, draft Matter, analysis job, analysis run

**Prototype Tenant**:
The single organizational boundary assumed by an isolated synthetic prototype environment. Every allowlisted practitioner within it can access every Matter Proposal and Matter; it is not a production firm or multi-firm tenancy model.
_Avoid_: Firm, production tenant
