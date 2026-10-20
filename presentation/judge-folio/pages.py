"""Representative editorial pages; content uses retained project evidence only."""

from layout import (BURGUNDY, CHALK, FOREST, HERE, INK, MUTED, ROOT,
                    WHITE, YELLOW, Page)

GITHUB = "https://github.com/alistairkung/private-client-graph"
PRODUCTION = "https://private-client-graph-production.up.railway.app"
PUBLICATION = GITHUB + "/blob/d5130917b32ba03e41d6345a8c3d604f4c906432/private_client_graph/published/research-results.v1.json"


def cover(canvas, number, evidence):
    page = Page(canvas, number, "FTEC5660 / Private Wealth", dark=True)
    page.heading("From documents to<br/>reviewable relationships", y=111,
                 size=54, color=WHITE)
    page.paragraph(
        "A Private Wealth tool for solicitors and advisers preparing an estate-planning "
        "or trust review: reconstruct family and trust relationships, inspect the "
        "documentary Evidence, and decide what to accept.",
        48, 256, 580, 17, 25, WHITE)

    # This editorial detail represents one actual Case 01 relationship.
    page.text("Alice Chen", 48, 405, 25, WHITE, "SansBold")
    page.text("Bob Chen", 672, 405, 25, WHITE, "SansBold", align="right")
    page.line(207, 417, 513, 417, WHITE, 1.2)
    page.line(513, 417, 506, 412, WHITE, 1.2)
    page.line(513, 417, 506, 422, WHITE, 1.2)
    page.rect(284, 397, 127, 36, FOREST)
    page.text("Parent of", 347.5, 409, 14, WHITE, align="center")
    page.line(348, 433, 348, 488, YELLOW, 1)
    page.rect(48, 488, 624, 176, YELLOW)
    page.text("Attendance Note - Meeting with Alice Chen", 70, 510, 11.5, INK, "SansBold")
    page.paragraph(
        "“Alice Chen confirmed that Alice Chen and David Chen are the parents of Bob Chen.”",
        70, 544, 570, 26, 31, INK, "Serif")
    page.paragraph(
        "A relationship is useful when the reader can inspect the words behind it.",
        48, 694, 585, 24, 29, WHITE, "Serif")
    page.text("University hackathon case study / English pages 1-20", 48, 789, 13, WHITE)
    page.text("Synthetic prototype. Simplified Chinese follows on page 21.", 48, 814, 12, WHITE)
    page.footer("Case 01: exact source-backed relationship; editorial diagram.",
                GITHUB + "/tree/main/cases/case_01")


def product_inspection(canvas, number, evidence):
    page = Page(canvas, number, "The reviewable Matter")
    page.heading("A graph you can question", y=83, size=43)
    page.paragraph(
        "An incoming adviser asks: what supports Bob Chen's connection to this family? "
        "Select Alice Chen's parent relationship, inspect the quoted words, then "
        "open the Source in context. Bob's beneficiary role needs separate Evidence.",
        48, 153, 624, 16, 23)

    capture = ROOT / "docs/artifacts/ui-consolidation/practitioner-evidence-desktop.png"
    page.image_detail(capture, (176, 234, 938, 803), 48, 250, 430)
    page.paragraph("Select the claim", 507, 268, 165, 19, 23, FOREST, "SansBold")
    page.paragraph(
        "Alice Chen is the parent of Bob Chen. Family relationships and Trust "
        "roles remain distinct claims.",
        507, 308, 165, 14, 20)
    page.paragraph(
        "The selected connector leads to the quotation below. Compare Bob's separate Trust role on page 3.",
        507, 431, 165, 14, 20, MUTED)
    page.text("Actual practitioner workspace: selected relationship detail", 48, 588, 11.5, MUTED)

    page.text("Source detail: Attendance Note - Meeting with Alice Chen", 48, 625, 11.5, MUTED)
    page.image_detail(capture, (969, 364, 1487, 444), 48, 652, 624)
    page.paragraph(
        "The quotation retains its Source identity. Selecting “View in source” "
        "reveals the passage in context; a highlighted sentence supports inspection "
        "but does not replace professional judgment.",
        48, 770, 624, 13, 18, INK)
    page.footer("Current UI capture; synthetic data and substituted model. PR #160.",
                GITHUB + "/pull/160")


def paired_experiment(canvas, number, evidence):
    page = Page(canvas, number, "Research methodology")
    page.heading("Change one stage.<br/>Keep the extraction fixed.", y=83, size=43)
    page.paragraph(
        "Can a name-only correction recover missed relationships without rewriting "
        "the claims? The comparison reuses saved extraction outputs and adds a "
        "zero-call replay control, isolating resolution from fresh extraction variability.",
        48, 196, 624, 16, 23)

    page.rect(48, 295, 624, 103, CHALK)
    page.text("A", 68, 319, 39, FOREST, "Serif")
    page.text("Fresh baseline extraction", 119, 316, 20, INK, "SansBold")
    page.paragraph("10 cases. One fresh model call per case.<br/>Retain all extraction outputs for reuse.",
                   119, 349, 500, 14, 20)
    page.line(360, 398, 360, 427, FOREST, 1.2)
    page.line(204, 427, 516, 427, FOREST, 1.2)
    page.line(204, 427, 204, 455, FOREST, 1.2)
    page.line(516, 427, 516, 455, FOREST, 1.2)
    page.text("A′", 48, 477, 37, BURGUNDY, "Serif")
    page.text("Exact replay", 113, 481, 20, INK, "SansBold")
    page.paragraph("Saved extraction<br/>No resolution<br/><b>0 provider calls</b>",
                   48, 529, 265, 16, 24)
    page.text("B", 382, 477, 37, FOREST, "Serif")
    page.text("With resolver", 439, 481, 20, INK, "SansBold")
    page.paragraph("Same saved extraction<br/>Model resolves alternative names<br/>for the same person<br/><b>10 additional provider calls</b>",
                   382, 529, 290, 15, 22)
    page.line(204, 627, 204, 643, FOREST, 1.2)
    page.line(516, 627, 516, 643, FOREST, 1.2)
    page.rect(48, 643, 624, 62, FOREST)
    page.text("Same deterministic construction and evaluation", 360, 664,
              17, WHITE, "SansBold", align="center")

    page.paragraph(
        "A′ reproduces A's outcomes. This helps isolate the resolver's effect "
        "from new extraction variability; it is <b>not an independent replication</b>. "
        "A′ and B use the same implementation and frozen inputs.",
        48, 738, 624, 15, 22)
    page.footer("Retained A / A′ / B records; post-hoc exploratory comparison.", PUBLICATION)


def measured_results(canvas, number, evidence):
    runs = {run["label"]: run["metrics"] for run in evidence["runs"]}
    baseline, resolved = runs["A"], runs["B"]
    page = Page(canvas, number, "Recorded findings")
    page.heading("Two corrections explain<br/>the entire gain", y=83, size=43)
    page.paragraph(
        "On 10 project-authored synthetic held-out cases, relationship micro-F1 "
        f'rose from <b>{baseline["micro_f1"]:.2%} to {resolved["micro_f1"]:.0%}</b>. '
        "The change came from two endpoint-name "
        "corrections for one person in one case.",
        48, 196, 624, 16, 23)

    capture = HERE / "assets/production-research-chart.jpg"
    page.image_detail(capture, (132, 765, 903, 1107), 48, 291, 624)
    page.paragraph(
        "Actual published Workbench chart. Run 1 = A; Run 2 = A′; Run 3 = B. "
        "The full 0-1 F1 scale is preserved; points are not a time trend.",
        48, 582, 624, 11.5, 16, MUTED)

    rows = [
        ("Matched relationships", str(baseline["tp"]), str(resolved["tp"])),
        ("Extra / missing relationships", f'{baseline["fp"]} / {baseline["fn"]}',
         f'{resolved["fp"]} / {resolved["fn"]}'),
    ]
    page.line(48, 634, 672, 634)
    page.text(f'Pooled across {evidence["benchmark"]["expected_relationships"]} expected relationships',
              48, 646, 12, MUTED)
    page.text("A / A′", 523, 646, 12, BURGUNDY, "SansBold", align="right")
    page.text("B", 659, 646, 12, FOREST, "SansBold", align="right")
    for index, (label, baseline_value, resolved_value) in enumerate(rows):
        top = 675 + index*31
        page.text(label, 48, top, 14)
        page.text(baseline_value, 523, top, 16, BURGUNDY, "SansBold", align="right")
        page.text(resolved_value, 659, top, 16, FOREST, "SansBold", align="right")

    page.rect(48, 743, 624, 86, CHALK)
    page.paragraph(
        f'<b>Evidence checks remained imperfect:</b> B passed {resolved["quote_passed"]}/{resolved["quote_assessed"]} approved-quote '
        f'checks and {resolved["source_pair_passed"]}/{resolved["source_pair_assessed"]} Source/quote-pair checks, using separate denominators. '
        "The resolver is implemented in the research pipeline; application intake "
        "currently uses baseline extraction. Small, synthetic, post-hoc comparison.",
        62, 753, 595, 13, 18)
    page.footer("Retained results and deployed chart, inspected 18 October 2026.",
                PRODUCTION + "/research-results#comparison")


SAMPLE_PAGES = [cover, product_inspection, paired_experiment, measured_results]
