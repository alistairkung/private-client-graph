"""Practitioner narrative pages grounded in authored Sources and real captures."""

from layout import CHALK, FOREST, INK, MUTED, ROOT, RULE, WHITE, Page


GITHUB = "https://github.com/alistairkung/private-client-graph"
PIN = GITHUB + "/blob/d5130917b32ba03e41d6345a8c3d604f4c906432/"
CAPTURES = ROOT / "presentation/product-demo/public/captures"


def original_problem(canvas, number, evidence):
    page = Page(canvas, number, "The original problem")
    page.heading("Reconstruct the facts.<br/>Keep the words within reach.", y=83, size=43)
    page.paragraph(
        "Before an estate-planning or trust review, a Private Wealth solicitor or "
        "adviser needs to establish the family relationships, recorded Trust roles "
        "and documents supporting each connection. PCG makes that factual map "
        "inspectable before advice.",
        48, 198, 624, 16, 23)

    page.rect(48, 329, 624, 208, CHALK)
    page.text("The question inside Case 01", 69, 349, 11.5, MUTED, "SansBold")
    page.paragraph(
        "“The purpose of the meeting was to establish an accurate understanding "
        "of the current family and beneficiary position before any further "
        "review or substantive advice is undertaken.”",
        69, 380, 580, 25, 30, INK, "Serif")
    page.text("Exact passage · Attendance Note – Meeting with Alice Chen", 69, 514, 11.5, MUTED)

    page.paragraph(
        "Across documents, a person may appear under another name and a later note "
        "may confirm or change a role. A <b>Matter</b> is the review workspace; "
        "<b>Sources</b> are its documents; <b>Evidence</b> is the quoted text behind "
        "each relationship. The map preserves the route back to those words.",
        48, 550, 624, 16, 23)
    page.paragraph(
        "<b>Built for this hackathon:</b> a relationship workspace, an AI-to-graph "
        "pipeline with deterministic checks, and a Workbench for controlled "
        "comparisons. The proposed benefit is a clearer factual handover: preparer "
        "and reviewer can inspect the same claims and supporting words. "
        "Practitioner usefulness remains to be tested.",
        48, 669, 624, 16, 23)
    page.line(48, 789, 672, 789)
    page.text("Reading route", 48, 803, 10.5, MUTED, "SansBold")
    page.text("Product 3-7  /  Method 8-12  /  Findings 13-17  /  Next 18-20", 169, 803, 11.5, MUTED)
    page.footer("Intended workflow: PRODUCT.md. Exact passage: Case 01 Source.",
                PIN + "cases/case_01/source.txt")


def distinct_claims(canvas, number, evidence):
    page = Page(canvas, number, "Family facts and Trust roles")
    page.heading("One person.<br/>Two different claims.", y=83, size=43)
    page.paragraph(
        "Bob Chen's family connection and his beneficiary status answer "
        "different questions. Case 01 states both explicitly. The graph must "
        "retain each relationship with its own supporting Evidence; one claim "
        "does not establish the other.",
        48, 196, 624, 16, 23)

    _claim_passage(
        page, 322, "Family relationship", "Alice Chen", "Bob Chen", "Parent of",
        "Alice Chen confirmed that Alice Chen and David Chen are the parents of Bob Chen.")
    _claim_passage(
        page, 518, "Trust role", "Bob Chen", "Evergreen Family Trust", "Beneficiary of",
        "Alice Chen confirmed that Bob Chen is a beneficiary of the Evergreen Family Trust.")

    page.paragraph(
        "The same note identifies Carol Wong as another beneficiary while "
        "recording no family relationship between Carol and the Chen family. "
        "A shared Trust connection is therefore not permission to add a family "
        "link. Documentary support governs what can be proposed.",
        48, 727, 624, 16, 23)
    page.footer("Case 01 Source and ground truth; editorial claim diagrams, not UI.",
                PIN + "cases/case_01/ground_truth.json")


def _claim_passage(page, y, category, source, target, relationship, quote):
    page.text(category, 48, y, 11.5, MUTED, "SansBold")
    page.text(source, 48, y + 26, 20, INK, "SansBold")
    page.text(target, 242, y + 26, 20, INK, "SansBold")
    page.line(177, y + 35, 221, y + 35, FOREST, 1)
    if relationship == "Parent of":
        page.line(221, y + 35, 215, y + 31, FOREST, 1)
        page.line(221, y + 35, 215, y + 39, FOREST, 1)
    page.text(relationship, 672, y + 30, 12, FOREST, align="right")
    page.line(48, y + 61, 672, y + 61, RULE)
    page.paragraph("“" + quote + "”", 68, y + 82, 587, 24, 29, INK, "Serif")


def synthetic_intake(canvas, number, evidence):
    page = Page(canvas, number, "From acquisition to proposal")
    page.heading("Several PDFs.<br/>One reviewable proposal.", y=83, size=43)
    page.paragraph(
        "An allowlisted signed-in user supplies a Matter reference, a title "
        "and one to five synthetic text-layer PDFs. Each document keeps its "
        "own Source identity and title. The documents are analysed together "
        "to produce one combined proposal.",
        48, 196, 624, 16, 23)

    page.image_detail(CAPTURES / "en-intake-files-page.png",
                      (130, 556, 895, 1145), 48, 322, 383)
    page.paragraph("Two distinct Sources", 455, 326, 217, 22, 26, FOREST, "Serif")
    page.paragraph(
        "The recorded intake uses “Family note” and “Trust roles”. The Source "
        "titles and selected PDFs shown here were entered in the real application.",
        455, 391, 217, 16, 23)
    page.paragraph(
        "Historical authenticated UI capture. Synthetic inputs; Google and "
        "model boundaries substituted. This records the workflow, not extraction accuracy.",
        455, 542, 217, 11.5, 16, MUTED)

    page.paragraph(
        "Deterministic PDF acquisition establishes the Authoritative Source "
        "text used for extraction, exact Evidence matching and later review. "
        "The raw PDFs are discarded after the intake request, including when "
        "processing fails; the reviewable record is the extracted text.",
        48, 654, 624, 16, 23)
    page.paragraph(
        "A proposal is saved only after successful analysis. It remains "
        "proposed state until the professional makes an explicit decision.",
        48, 773, 624, 16, 23)
    page.footer("PDF acquisition: ADR 0005. Historical capture provenance in product-demo/.",
                PIN + "docs/adr/0005-treat-extracted-pdf-text-as-the-authoritative-source.md")


def professional_acceptance(canvas, number, evidence):
    page = Page(canvas, number, "Professional acceptance")
    page.heading("The decision belongs<br/>to the professional.", y=83, size=43)
    page.paragraph(
        "A mechanically valid graph is still a machine proposal. The saved "
        "proposal can be reopened for review; it does not silently become a "
        "Matter. The professional inspects the complete graph and supplied "
        "Sources, then confirms the whole proposal or discards the intake.",
        48, 196, 624, 16, 23)

    page.text("Actual whole-proposal decision", 48, 322, 11.5, MUTED, "SansBold")
    page.image_detail(CAPTURES / "en-confirmation-page.png",
                      (130, 1378, 1310, 1576), 48, 349, 624)
    page.paragraph(
        "Historical authenticated capture, before confirmation. The local "
        "model was substituted; proposal confirmation and persistence used "
        "the real application paths.",
        48, 466, 624, 11.5, 16, MUTED)

    page.rect(48, 529, 624, 103, FOREST)
    page.text("Proposed", 69, 547, 11.5, WHITE, "SansBold")
    page.text("Explicit confirmation", 360, 551, 16, WHITE, align="center")
    page.text("Accepted current state", 651, 600, 11.5, WHITE, "SansBold", align="right")
    page.line(69, 589, 651, 589, WHITE, 1)
    page.line(651, 589, 644, 584, WHITE, 1)
    page.line(651, 589, 644, 594, WHITE, 1)

    page.paragraph(
        "Confirmation records the practitioner's decision to adopt the whole "
        "proposed map for the Matter; each claim retains its Sources for further "
        "checking. The recorded demonstration saves that state, reopens the Matter "
        "and inspects a parent relationship without reanalysis.",
        48, 666, 624, 16, 23)
    page.paragraph(
        "This is whole-proposal acceptance. Per-relationship editing and "
        "incremental updates to an existing Matter are outside this workflow.",
        48, 785, 624, 16, 23)
    page.footer("Recorded transaction, confirmation and reopen: product-demo/PROVENANCE.md.",
                PIN + "presentation/product-demo/PROVENANCE.md")


def multiple_sources(canvas, number, evidence):
    page = Page(canvas, number, "Source-specific corroboration")
    page.heading("One relationship.<br/>More than one Source.", y=83, size=43)
    page.paragraph(
        "In authored Case 04, Andrew Chan's beneficiary relationship to the "
        "Hillcrest Family Trust appears in the first meeting and is confirmed "
        "at a follow-up. The relationship can carry Evidence from both Sources, "
        "with each quotation attributed to its own text.",
        48, 196, 624, 16, 23)

    capture = ROOT / "docs/artifacts/ui-consolidation/curated-multiple-sources-desktop.png"
    page.text("Current UI detail: two supporting Sources", 48, 320, 11.5, MUTED, "SansBold")
    page.image_detail(capture, (938, 305, 1512, 452), 48, 347, 624)
    page.text("Source 2 · sources/note_02.txt · note_02_evidence_001", 48, 532, 11.5, MUTED)
    page.image_detail(capture, (938, 760, 1512, 890), 48, 560, 624)
    page.paragraph(
        "Curated authored ideal in the current review workspace. This is "
        "synthetic demonstration data, not a model outcome or accepted Matter.",
        48, 715, 624, 11.5, 16, MUTED)
    page.paragraph(
        "The second note supplements the first rather than revising it. "
        "Corroboration here does not demonstrate general conflict resolution, "
        "temporal reasoning or automatic updates to an accepted Matter.",
        48, 767, 624, 16, 23)
    page.footer("Exact follow-up passage and Source identity: authored Case 04.",
                PIN + "cases/case_04/sources/note_02.txt")
