# Matter Intake slice

> **Status:** Accepted design; implementation pending and not yet authorized.

## Goal

Design the smallest coherent practitioner workflow that begins before a Matter exists in Private Client Graph and ends with one complete persisted Matter open in the existing review workspace:

```text
externally governed Matter reference and title
    + one PDF acquisition file
    -> deterministic text extraction
    -> one finalized Authoritative Source
    -> probabilistic relationship extraction
    -> deterministic proposal validation
    -> durable Matter Proposal awaiting confirmation
    -> practitioner confirmation
    -> one complete persisted Matter with an accepted current Canonical Graph
    -> existing professional review workspace
```

The slice must preserve the separation between probabilistic semantic extraction, deterministic validation and graph construction, application orchestration, persistence, and presentation. It does not change extraction contracts, relationship semantics, graph canonicalisation, provenance rules, evaluation, or benchmark ground truth.

## Intended data and access boundary

This is a product-concept prototype for synthetic material only. It must not be described as suitable for real confidential client information.

One isolated deployment is one Prototype Tenant. Named practitioners authenticate through Google Identity using OIDC and must be present in a deployment-configured allowlist. Authorization uses Google's stable provider subject identifiers rather than mutable email addresses; email is display information only. No passwords or user accounts are stored by Private Client Graph. The implementation targets only Google and introduces no provider-neutral abstraction, provider-selection UI, multiple issuers, or identity linking.

After server-side Google OIDC authentication, the backend issues a short-lived, framework-managed application session. Google establishes identity; Private Client Graph authorizes the stable Google `sub` against the current deployment allowlist on every authenticated request. The browser receives only a secure, HTTP-only application-session cookie. Google tokens are never exposed to frontend JavaScript or browser storage, and the application retains no Google access or refresh token because it calls no Google APIs.

All cookie-authenticated state-changing practitioner APIs require established framework or library protection against CSRF and untrusted origins. The application provides logout and uses a short configurable session lifetime that requires reauthentication after expiry. It stores no persisted user or session records and does not hand-roll session cryptography or CSRF mechanisms; the security properties are authoritative while concrete library mechanics remain an implementation decision.

### Fail-closed deployment configuration

The deployment that enables Matter Intake validates all required Google OIDC, application-session, non-empty subject-allowlist, model-provider, and authenticated-analysis-allowance configuration before serving traffic. Missing or invalid configuration fails startup or readiness for the combined deployment.

There is no fallback authentication, empty-allowlist bypass, unlimited-analysis mode, silently disabled creation path, or unprotected practitioner route. This operational release boundary does not couple Public Showcase and practitioner application orchestration; it ensures that the combined service is deployed only as one correctly configured unit.

Every allowed practitioner can create, list, review, confirm, and discard Matter Proposals and can list and review every Matter in that deployment. There is no per-user ownership, assignment, role, per-resource access-control list, or persisted Firm or Tenant model.

The access boundary is path-specific:

- the Public Showcase and `/api/showcase/*` remain public;
- the entire `/app` subtree and all `/api/matter-proposals*` and `/api/matters*` operations require authentication and allowlist authorization;
- practitioner APIs enforce the boundary independently of frontend routing.

### Practitioner account and application navigation

The Practitioner Application keeps **Matters** visible as its sole primary
navigation item throughout the `/app` subtree. A compact circular **account and
application menu** is the single entry point for the two secondary actions
available to an authenticated practitioner:

1. **Public showcase**, which navigates to `/`;
2. **Sign out**, which uses the existing protected logout operation.

This is deliberately not a general user or profile menu. It exposes no name,
email address, initials, profile, settings, notifications, role, Firm, or tenant
selection. Its trigger uses a neutral account symbol because the frontend has no
display-identity contract and must not infer authentication or identity from
frontend-only state. Moving Sign out into this menu does not change the
framework-managed session, CSRF, trusted-origin, allowlist, or logout security
model.

The public `/` surface does not render this account control, including when the
browser happens to hold a valid practitioner session. It retains a visible
**Practitioner application** link. Following that link navigates to `/app` and
allows the existing server-enforced authentication boundary to begin Google
sign-in when required; the public frontend does not determine authentication
state or render a separate Sign in action.

The persistent synthetic-only notice remains visible in practitioner content.
It is a data-handling boundary, not account information, and must not move into
the menu.

This prototype authorization model is not the eventual multi-firm production architecture. Actual confidential client information would first require a separate design covering tenancy and data ownership, Matter authorization, provider and data-processing approval, retention, logging, backups, incident controls, and other applicable operational and legal safeguards. Basic authentication alone would not satisfy that requirement.

### Synthetic-only submission gate

The authenticated Practitioner Application displays a persistent notice that the prototype accepts synthetic or fictional material only. Every Matter Proposal creation request also requires the practitioner to explicitly confirm that the uploaded material is synthetic or fictional.

The frontend requires this confirmation before submission, and the Matter Proposal creation API independently requires it before PDF parsing, model invocation, or persistence. The confirmation is a request gate only: the application does not persist it or present it as an audit, compliance, classification, or security control. Authentication, allowlisting, and attestation do not make the prototype suitable for real confidential client information.

## Source acquisition

The slice accepts exactly one PDF. PDF is an acquisition format, not a Matter or domain representation:

```text
PDF upload
    -> deterministic text extraction
    -> finalized Authoritative Source text
```

Only text-layer PDFs are supported. Scanned or image-only PDFs and OCR are explicitly unsupported. Native email ingestion is not required; an email may be exported to PDF and follows the same path. Source genre remains independent of acquisition infrastructure, allowing later cases to exercise attendance notes, emails, letters, trust documents, or similar material without separate ingestion mechanisms.

The finalized extracted text is the Authoritative Source. It is persisted, sent unchanged to semantic extraction, displayed in Matter Proposal and Matter review, and used for exact Evidence occurrence validation. The PDF is held only for the active request and is discarded whether extraction or later processing succeeds or fails. It is never persisted as proposal or Matter state, a run artifact, or a document resource.

The intake form requires an explicit Authoritative Source title in addition to external Matter reference, Matter title, PDF, and the synthetic-only confirmation. The browser may prefill that title from the uploaded filename stem, but the practitioner can confirm or edit it before submission. Only the resulting Source title is persisted; the original filename, PDF metadata, and submission confirmation are not stored separately or treated as domain values.

### Minimal canonical normalization

Deterministic PDF extraction:

- processes pages in PDF order;
- canonicalizes line endings;
- inserts one specified deterministic separator between pages;
- removes invalid control characters;
- otherwise preserves extracted Unicode, spacing, punctuation, and line breaks.

It does not dehyphenate wrapped words, collapse internal whitespace, remove repeated headers or footers, infer column order, reconstruct paragraphs, or use a model to clean the text. The finalized value becomes immutable before semantic extraction: the same value crosses extraction, persistence, Evidence validation, and review boundaries. Parser-version changes may affect future intake attempts but never rewrite an existing Matter's Authoritative Source.

### Admission envelope

The application accepts one upload and enforces all limits server-side before semantic extraction:

- maximum upload size: 10 MiB;
- maximum length: 50 pages;
- maximum finalized Authoritative Source: 100,000 Unicode characters;
- minimum length: one page containing at least one non-whitespace extracted character.

The `.pdf` filename extension and browser `application/pdf` media type are advisory. The server verifies the PDF signature and requires successful parsing. These limits are explicit application configuration rather than domain semantics. Exceeding a limit produces a clear validation failure and creates no Matter.

### Acquisition failures

PDF acquisition is a strict pre-analysis gate:

- encrypted PDFs are unsupported and rejected without requesting a password;
- malformed or parser-rejected PDFs are rejected as invalid;
- image-only, scanned, empty, or otherwise textless PDFs are rejected as non-extractable, with clear notice that OCR is unsupported;
- admission-limit failures identify the exceeded limit;
- an unexpected deterministic-extraction service failure is reported as an acquisition failure and may be retried with the same file.

No acquisition failure invokes the model, creates a Matter, or retains the upload or extracted text. Correctable failures direct the practitioner to select a corrected or different PDF and submit again. These failures are not failed Matters or analysis lifecycle states.

### No pre-analysis confirmation

The practitioner does not preview or confirm extracted text before semantic analysis. One explicit creation action may proceed from successful PDF validation and deterministic extraction into analysis. On complete success, the Matter Proposal review page displays the finalized Authoritative Source alongside its proposed Canonical Graph and Evidence by reusing the existing review components; viewing that source does not constitute professional approval.

A pre-analysis preview would require a trustworthy cross-request temporary-intake lifecycle, repeated upload and extraction, or a signed client-held representation. This slice introduces none of those. If observed PDF reading-order failures or later use with real documents make preflight confirmation necessary, that workflow requires a separate design.

## Synchronous analysis and pre-Matter confirmation

`Matter.current_graph` means the professionally accepted current relationship state, not merely the latest machine-produced analysis. Deterministic validity and professional acceptance are separate.

Matter Intake therefore has two semantic stages:

```text
upload and analyse
    -> durable Matter Proposal awaiting confirmation
confirm whole proposal
    -> complete Matter
```

The first stage remains one synchronous application operation:

1. require the synthetic-only submission confirmation;
2. validate Matter metadata and the PDF admission envelope;
3. deterministically extract and minimally normalize the Authoritative Source text;
4. invoke probabilistic semantic extraction once;
5. run the existing deterministic graph construction and provenance validation;
6. persist the resulting Canonical Graph as `MatterProposal.proposed_graph` with its Authoritative Source.

No database transaction remains open during PDF processing or model invocation. PDF parsing, normalization, and deterministic validation are local operations; the model invocation is the only materially slow external boundary and is already proven workable synchronously in the Public Showcase. This slice introduces no queues, background workers, polling, or analysing status.

A Matter Proposal contains practitioner-review state: proposed Matter identity, the Authoritative Source, and a mechanically valid `proposed_graph` awaiting explicit confirmation. It is created only after successful synchronous analysis, is not an incomplete Matter, and does not contain opaque provider output for debugging. `ExtractionResult` and `RelationshipCandidate` values remain request-local and are discarded after successful graph construction; candidates and graph are never both persisted.

The persisted shape is deliberately minimal:

```text
MatterProposal
- id                         opaque internal UUID
- external_reference         copied to Matter
- matter_title               copied to Matter
- authoritative_source
    - title                  copied to Matter
    - text                   copied to Matter
- proposed_graph             validated CanonicalGraph, copied unchanged
```

Existence means “awaiting confirmation,” so there is no status column. The Matter Proposal has its own route identity and does not receive a Matter UUID early. Because every practitioner in the Prototype Tenant has equal access, there is no creator or owner field. It stores no timestamps, PDF metadata, original filename, provider response, candidates, parser or model versions, error details, or review-decision fields. The same Canonical Graph and source/Evidence consistency validation applies whenever the proposal crosses the application boundary.

Only explicit whole-proposal confirmation may create a complete Matter and copy the reviewed `proposed_graph` unchanged into its accepted `current_graph`. Confirmation does not rerun extraction or graph construction. This slice introduces no editing, per-relationship acceptance or rejection, correction, rejection reasons, or partial confirmation. Disagreement handling requires a subsequent workflow decision.

### Atomic confirmation

Confirmation atomically consumes the Matter Proposal in one short database transaction:

1. lock and reload the Matter Proposal;
2. revalidate its persisted Authoritative Source, `proposed_graph`, and exact source/Evidence consistency;
3. generate a new Matter UUID;
4. insert the complete Matter by copying the reviewed identity, source, and graph unchanged;
5. delete the Matter Proposal;
6. commit and return the Matter UUID for navigation to its workspace.

Failure to insert or delete rolls back the transaction and leaves the Matter Proposal available. Concurrent confirmation permits exactly one Matter creation. A successful promotion retains no Matter Proposal, tombstone, proposal copy, promotion history, or idempotency record.

Confirmation is duplicate-safe but deliberately not replay-successful. If the transaction commits but its HTTP response is lost, the application cannot determine from a repeated Matter Proposal request which Matter was created. It must describe the outcome as unknown and direct the practitioner to the Matter Ledger to determine whether the Matter exists, rather than asserting that confirmation failed. Replay-safe confirmation is a future requirement only if real usage shows this ambiguity is materially problematic.

### Whole-intake discard

**Discard intake** is the negative terminal path for pre-Matter state. It means only that the practitioner no longer wants to retain that intake attempt; it is not professional rejection of any relationship and is not evidence that the AI output was incorrect.

After explicit confirmation of the destructive action, the application atomically deletes the Matter Proposal, including its Authoritative Source and proposed graph, creates no Matter, and retains no rejection reason, tombstone, audit record, or other copy. Per-relationship disagreement, correction, and rejection semantics remain explicitly deferred.

### Curated synthetic initialization

The existing Evergreen seed remains a complete, pre-accepted synthetic Matter even though it was constructed directly from the curated Case 01 ideal-extraction fixture. This is an explicit backend-controlled initialization exception for known synthetic reference state. It is not callable through the application and is not a precedent for allowing practitioner-supplied material to bypass the `MatterProposal -> confirmation -> Matter` boundary.

## Matter Proposal discovery

The practitioner entry point at `/app` presents two visibly and semantically separate collections:

- the Matter Ledger containing complete accepted Matters;
- an **Awaiting confirmation** collection containing Matter Proposals.

Each pending row shows only external Matter reference and Matter title and opens `/app/matter-proposals/{proposal_id}`. Collection placement and row existence communicate the state; there is no status field or status chip. The collection includes no assignee, age, priority, metrics, activity, or other task-management chrome. Every allowlisted practitioner in the Prototype Tenant may open and confirm or discard any Matter Proposal.

## Practitioner journey

Matter Intake uses dedicated pages rather than a modal or wizard:

```text
/app
    -> Create Matter
/app/matter-proposals/new
    -> external reference, Matter title, Source title, PDF, synthetic-only confirmation
    -> Upload and analyse
    -> wait for synchronous response
/app/matter-proposals/{proposal_id}
    -> review proposed graph and exact Evidence against the Authoritative Source
    -> Confirm and create Matter OR Discard intake
/app/matters/{matter_id} OR /app
```

The Matter Proposal page reuses the existing graph, Authoritative Source, Evidence, and exact-highlight review components but clearly identifies the graph as proposed. It adds only the two earned terminal actions and no editing controls, stepper, dashboard metrics, analysis history, or workflow-status chrome. Dedicated routes support truthful refresh and direct re-entry.

### Static synthetic-source prompt

The proposal-creation page includes a secondary **Need something to try?** affordance. It opens a modal containing a copyable, static prompt for use with an external AI assistant. The prompt encourages a completely fictional private-client source in a realistic genre such as an attendance note, client email, or letter; fictional people and trusts; and relationships supported naturally in the prose. It explicitly prohibits real personal or client information and tells the practitioner to export the result as a text-layer PDF for normal upload.

This is a demo convenience only. Opening or copying the prompt performs no model call, network request, provider integration, document generation, PDF generation, or persistence. The generated PDF follows the ordinary admission, analysis, and synthetic-only attestation path. Exact modal styling and wording are reversible presentation details provided these boundaries remain true.

## External Matter reference

The practitioner supplies the Matter reference assigned by the firm's existing ecosystem. Private Client Graph does not generate or govern it.

Within one Prototype Tenant, the same external Matter reference may identify at most one Matter Proposal or accepted Matter. Proposal creation rejects a duplicate found in either collection, and the check must remain concurrency-safe across application replicas. Atomic confirmation transfers the already-reserved reference from Matter Proposal to Matter without opening a duplicate-creation race.

The reference is an opaque label with this validation contract:

- trim leading and trailing whitespace and require a non-empty result;
- allow at most 100 Unicode characters;
- reject control characters and line breaks;
- preserve internal whitespace, punctuation, separators, and supplied letter case for display;
- impose no format regex, parsed components, or generated prefix;
- compare the trimmed value with Unicode case folding for duplicate detection;
- otherwise never rewrite the persisted display value.

More aggressive normalization could incorrectly merge distinct externally governed values and is not permitted.

Matter title and Authoritative Source title each use the same minimal opaque-text contract: trim leading and trailing whitespace; require a non-empty result; allow at most 200 Unicode characters; reject control characters and line breaks; and otherwise preserve internal whitespace, punctuation, and case. Neither title is unique or semantically parsed.

### Atomic reference claim

PostgreSQL owns cross-resource uniqueness through a narrow `external_matter_reference_claims` table:

```text
canonical_reference  primary key
resource_kind        matter_proposal | matter
resource_id          UUID
```

Matter Proposal creation inserts the claim and proposal in one transaction. A conflicting primary key identifies the existing resource without a provider call in the normal preflight case and remains authoritative for concurrent races. Confirmation inserts the Matter, moves the claim to its new kind and UUID, and deletes the proposal in one transaction. Discard deletes both proposal and claim atomically. The claim stores no Firm, Tenant, history, timestamps, or display metadata and is not a route identity or generalized identity registry.

The schema change requires a new Alembic migration. Existing applied migrations remain immutable, and the curated Evergreen Matter receives its corresponding claim during migration or explicit initialization without becoming dependent on benchmark fixtures at runtime.

If any stage before durable Matter Proposal creation fails, the application persists neither a Matter Proposal, Matter, nor Authoritative Source and retains no uploaded PDF server-side. Every persisted Matter remains complete and immediately reviewable.

An analysis that finds no supported relationships still produces a valid Matter Proposal with an empty `proposed_graph`. The confirmation view clearly distinguishes “analysis completed with no proposed relationships” from analysis failure. Because an empty result could mean either a legitimately irrelevant source or a model omission, deterministic code does not impose a minimum-edge rule; the practitioner may confirm the empty graph as the Matter's accepted current state.

### Analysis failure and retry

The application performs no automatic model retry. Retry remains an explicit practitioner action:

- a transient provider failure offers **Retry analysis**;
- a non-transient provider or configuration failure reports that analysis is unavailable without encouraging repeated retry;
- invalid structured model output or deterministic graph/provenance rejection reports that no valid proposal was produced and permits a fresh analysis attempt;
- a known transactional rollback states that no Matter Proposal was saved and permits retry;
- a commit or response failure whose outcome cannot be proven is reported as ambiguous, never as a definite failure.

Before any retry invokes the model, the application resolves the canonical external Matter reference across Matter Proposals and accepted Matters. If a Matter Proposal now owns it, return or navigate to that proposal; if a Matter owns it, return or navigate to that Matter. Only absence from both collections permits a new complete analysis attempt using form values and the PDF still held locally by the browser. This is narrow domain-key recovery, not a general retry or idempotency subsystem.

Failed attempts retain no extracted text, candidate set, or graph server-side. Duplicate-reference checking occurs before model invocation and again under the authoritative atomic uniqueness mechanism while persisting the Matter Proposal, avoiding unnecessary calls in the normal case and closing concurrent-creation races.

### Authenticated analysis allowance

Matter Proposal analysis has a separate configurable deployment-wide fixed-window provider-attempt allowance shared by all allowlisted practitioners. It is persistent operational state, not Matter Proposal, Matter, practitioner, or review state. It remains separate from the Public Showcase allowance even if both use the same lower-level atomic quota capability.

After authentication, attestation, metadata validation, PDF acquisition, and the initial duplicate-reference check succeed, the application atomically consumes one allowance slot immediately before invoking the provider. Provider, structured-output, graph-validation, and later persistence failures do not refund an attempt. Rejected requests that never reach the provider do not consume one.

Exhaustion prevents new model invocation and reports when the allowance resets, while existing Matter Proposals, Matters, review, confirmation, and discard remain available. The application exposes no per-practitioner counters, roles, quota administration, or usage dashboard.

## Practitioner API

The authenticated practitioner API represents Matter Proposals and Matters as separate resources:

```text
GET    /api/matter-proposals
POST   /api/matter-proposals
GET    /api/matter-proposals/{proposal_id}
DELETE /api/matter-proposals/{proposal_id}

GET    /api/matters
POST   /api/matters
GET    /api/matters/{matter_id}
```

`POST /api/matter-proposals` accepts authenticated `multipart/form-data` containing external Matter reference, Matter title, Authoritative Source title, one PDF, and the required synthetic-only confirmation. Success returns `201 Created` with the persisted proposal and its resource location. The collection returns only proposal ID, external reference, and Matter title; detail returns the Authoritative Source and `proposed_graph`.

`POST /api/matters` accepts only a Matter Proposal identifier. It is the confirmation operation expressed as creation of a Matter resource: the server atomically locks and consumes that proposal, creates the accepted Matter, and returns `201 Created` with the new Matter and its resource location. The API accepts no arbitrary Source or graph payload at this endpoint, so there is no general bypass around proposal confirmation.

`DELETE /api/matter-proposals/{proposal_id}` atomically discards the whole proposal and returns no retained representation. The UI obtains explicit destructive confirmation before issuing the request.

A duplicate external reference returns a typed `409 Conflict` identifying whether the existing resource is a Matter Proposal or Matter and providing its resource location, allowing the frontend to navigate without invoking the model again. Raw extraction, candidates, provider data, benchmark data, and acquisition PDFs never cross this API.

## Testing boundary

Deterministic CI substitutes only the stochastic model boundary with a known `ExtractionResult` and keeps PDF extraction, graph construction, PostgreSQL persistence, API orchestration, and browser behavior real.

Focused backend coverage includes:

- deterministic PDF normalization and each admission/failure category using committed synthetic fixtures;
- authentication, allowlist, origin, CSRF, and synthetic-attestation gates occurring before PDF parsing or provider invocation;
- provider-attempt consumption and exhaustion independent from Public Showcase quota;
- real graph construction, empty proposals, source/Evidence integrity, and absence of retained candidates;
- the full Alembic chain on PostgreSQL, including Matter Proposals, reference claims, and operational quota state;
- cross-resource reference conflicts and concurrent proposal creation;
- atomic confirmation, concurrent terminal actions, rollback behavior, claim transfer, and unchanged graph promotion;
- atomic discard and complete removal of Source, graph, and reference claim;
- safe handling of corrupt persisted proposal state and known versus ambiguous persistence outcomes.

Browser coverage uses a substituted Google identity and model boundary and exercises:

```text
authenticate as an allowlisted practitioner
-> open /app
-> create a Matter Proposal from a real synthetic text-layer PDF
-> review a relationship and its exact Evidence
-> confirm and open the resulting Matter
-> refresh the Matter workspace
```

A second focused journey covers whole-proposal discard. Existing Public Showcase and persisted-Matter journeys remain protected. Live-model behavior continues to be measured outside deterministic CI through benchmark evaluation rather than asserted as a stable test result.

## Derived retrieval state

Retaining the PDF is not required for future semantic retrieval. If larger or multiple source corpora later earn retrieval-augmented generation, chunks, embeddings, and vector indexes derive from persisted Authoritative Source text. Those artifacts are rebuildable derived state and must not replace exact Evidence provenance. No retrieval infrastructure is part of this slice.

## Practitioner-validated future acquisition requirement

A practising private-client lawyer has identified direct document-management-system acquisition, particularly iManage, as desirable in a future version. This is practitioner-validated product evidence, but it is entirely outside this slice. Native email integration has not been identified as a current requirement.

## Explicitly excluded source capabilities

- multiple source documents;
- retained or downloadable acquisition PDFs;
- scanned-document or image-only PDF support;
- OCR;
- native email ingestion;
- iManage or other document-management-system integration;
- general document management;
- PDF-native Evidence coordinates or visual reproduction;
- retrieval, chunking, embeddings, or vector indexes.

## Intended safety level and deferred production requirements

The resulting system is intended only for allowlisted prototype practitioners using synthetic or fictional material. Google authentication, deployment allowlisting, CSRF protection, a synthetic-only attestation, and a model-usage allowance make that prototype boundary credible; they do not make the application suitable for actual confidential client information.

Before any real client data is accepted, a separate production design must address at least:

- firm tenancy and durable data ownership;
- Matter-level authorization, roles, access changes, and account lifecycle;
- auditable professional acceptance, including who acted and when;
- identity-provider and firm SSO requirements beyond this Google-only prototype;
- model-provider approval, contractual data use, retention, residency, and confidentiality;
- source and Matter retention, deletion, legal hold, backup, and recovery;
- security logging, monitoring, incident response, and administrative access;
- encryption and key-management requirements;
- document-malware and parser-isolation requirements appropriate to real uploads;
- security, privacy, and legal review of the complete deployed system.

Those requirements must be designed before relaxing the synthetic-only guardrail; they are not incremental polish on this slice.

## Practitioner validation questions

The material design decisions are settled, but these questions should be tested with practising lawyers rather than answered by assumption:

- Is a 50-page single-source limit sufficient for the representative documents they would use first?
- Is exporting attendance notes, emails, letters, and similar sources to text-layer PDF a credible interim acquisition workflow?
- Is whole-proposal confirmation useful without correction, or does the next product slice need per-relationship disagreement and correction immediately?
- What metadata should a future iManage acquisition preserve once that practitioner-validated integration requirement is designed?
