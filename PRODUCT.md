# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary users are private-client solicitors and advisers reviewing family and trust relationships in the context of a Matter. They need to inspect machine-proposed relationships against the exact source passages that support them, then decide whether the complete proposal should become accepted current Matter state.

Public visitors, researchers, and evaluators are a secondary audience. The Public Showcase explains the product through fixed synthetic material, while benchmark tooling measures extraction and provenance quality outside the practitioner workflow.

## Product Purpose

Private Client Graph is an emerging practitioner product for reconstructing reviewable family and trust relationship graphs from private-client source material. It keeps source Evidence attached to every relationship so a professional can move between the graph and the precise text supporting it.

The benchmark research supports the practitioner product: it makes extraction and provenance quality measurable without turning benchmark scores into professional-review judgments.

Current success means a practitioner can identify a Matter, review its Authoritative Source and proposed Canonical Graph together, inspect exact Evidence for each relationship, and explicitly confirm the complete proposal before it becomes professionally accepted current Matter state.

## Positioning

The product combines probabilistic interpretation with deterministic validation and graph construction. Its defining mechanism is evidence-first relationship review: extracted family and trust relationships remain traceable to exact source text, while machine proposals, professional acceptance, and offline benchmark evaluation remain distinct states and activities.

## Operating Context

The practitioner experience is Matter-oriented. A Matter is the primary work object and uses an externally supplied Matter reference from the firm's existing ecosystem. People and trusts remain entities within the Matter's Canonical Graph rather than becoming separate navigation roots.

The current intake and review ritual is:

1. Supply Matter identity and a synthetic or fictional text-layer PDF.
2. Deterministically establish the Authoritative Source and run semantic extraction.
3. Construct and validate a proposed Canonical Graph.
4. Review the proposed relationships beside their exact supporting Evidence.
5. Confirm the complete proposal into current Matter state, or discard the intake.

The Public Showcase is a separate, explicitly synthetic research and product-demonstration journey. Benchmark Evaluation is also separate from Professional Review.

## Capabilities and Constraints

- Supported entity types are `person` and `trust`.
- Supported relationship types are `parent_of`, `sibling_of`, `spouse_of`, `settlor_of`, `trustee_of`, and `beneficiary_of`.
- Every relationship requires exact source Evidence.
- Semantic extraction is probabilistic; validation, graph construction, canonicalisation, identity handling, and evaluation are deterministic.
- A Matter Proposal is machine-proposed review state. A Matter's current graph is professionally accepted state.
- The present prototype accepts only synthetic or fictional material. It must not accept real client or personal information.
- Real client material is an intended future direction only after authentication, Matter authorization, tenancy and ownership, security, privacy, data handling, and related requirements have been fully scoped and implemented.
- Richer identity resolution, temporal state, contradictions, multi-source aggregation, per-relationship correction, and other semantics remain undecided until concrete product or benchmark evidence earns them.

## Brand Commitments

The product name is **Private Client Graph**. Product language is professional, precise, evidence-led, and candid about the prototype's limits. Use the established domain terms in `GLOSSARY.md`, especially Matter, Matter Proposal, Authoritative Source, Canonical Graph, Evidence, Professional Review, Public Showcase, and Benchmark Evaluation.

Do not imply production readiness, security or compliance guarantees, adoption, accuracy, or professional judgment that the available evidence does not support.

## Evidence on Hand

- Synthetic Benchmark Cases include source documents, known relationship answer keys, and approved Evidence spans.
- Case 01 provides the Evergreen synthetic example used by the Public Showcase and seeded practitioner experience.
- The repository contains deterministic unit, integration, and browser journeys covering extraction boundaries, graph construction, Matter workflows, relationship selection, and exact Evidence highlighting.
- Offline evaluation reports relationship precision, recall, F1, and provenance accuracy for benchmark runs.
- A practising private-client lawyer has identified direct document-management-system acquisition, particularly iManage, as desirable in a future version. The workflow and metadata requirements remain undecided.
- There are no approved testimonials, customer logos, pricing claims, adoption claims, or production security/compliance claims; future product work must not fabricate them.

## Product Principles

1. **Evidence before assertion.** Every relationship remains inspectable against exact source text.
2. **Professional acceptance is explicit.** Mechanically valid machine output does not become current Matter state without practitioner confirmation.
3. **Separate interpretation from mechanics.** Use the model for source semantics and deterministic code for validation, identity, canonicalisation, persistence boundaries, and evaluation.
4. **Earn complexity through evidence.** Add product capabilities and graph semantics only in response to demonstrated practitioner or benchmark needs.
5. **Protect client trust before expanding scope.** Real client material is out of bounds until the complete security, authorization, tenancy, privacy, and data-handling design is implemented.

## Accessibility & Inclusion

Core practitioner journeys must remain keyboard operable, preserve visible focus, and support responsive layouts. Existing interaction specifications require usable focus order and minimum 44-pixel pointer targets for primary controls. No formal accessibility conformance target has yet been recorded.
