"""Research chapter figures, drawn from the retained publication passed by the builder."""

from html import escape

from layout import BURGUNDY, CHALK, FOREST, INK, MUTED, WHITE, YELLOW, Page

GITHUB = "https://github.com/alistairkung/private-client-graph"
PUBLICATION = GITHUB + "/blob/d5130917b32ba03e41d6345a8c3d604f4c906432/private_client_graph/published/research-results.v1.json"
VALIDATION = GITHUB + "/tree/d5130917b32ba03e41d6345a8c3d604f4c906432/research/final-day/validation"
ROADMAP = GITHUB + "/blob/d5130917b32ba03e41d6345a8c3d604f4c906432/cases/README.md"


def research_method(canvas, number, evidence):
    page = Page(canvas, number, "Research / how we developed PCG")
    page.heading("A case-led method,<br/>from hypothesis to product", size=42)
    page.paragraph(
        "The methodology starts with a documentary challenge. Development "
        "examples make the expected behaviour explicit; separate held-out "
        "examples test it. The Workbench makes the outcomes inspectable, and "
        "the surrounding application supports the workflow.",
        48, 196, 624, 16, 23)
    steps = [
        ("Author a case hypothesis",
         "Define the new difficulty and what to hold stable, so a failure can be diagnosed."),
        ("Build development test cases",
         "Write synthetic Source samples and explicit ground-truth relationships and Evidence."),
        ("Build a separate held-out test set",
         "Create new synthetic situations and check their truth separately from authoring."),
        ("Measure and plot in the Workbench",
         "Compare frozen runs, inspect relationship and Evidence scores, and trace errors to Sources."),
        ("Build the surrounding application",
         "Support document intake, graph and Evidence inspection, and explicit professional acceptance."),
    ]
    page.line(64, 336, 64, 722, FOREST, 1)
    for index, (title, explanation) in enumerate(steps):
        top = 320 + index * 94
        page.circle(64, top+15, 16, FOREST)
        page.text(str(index+1), 64, top+8, 15, WHITE, "SansBold", align="center")
        page.text(title, 100, top, 21, FOREST, "SansBold")
        page.paragraph(explanation, 100, top+33, 572, 14, 20, max_height=44)
    page.paragraph(
        "<b>Hackathon scope:</b> baseline extraction plus constrained alias resolution. "
        "The roadmap on page 19 sets out the broader programme; it is not a list of completed experiments.",
        48, 791, 624, 13, 18)
    page.footer("Author's methodology; case hypotheses, held-out records and Workbench implementation.", ROADMAP)


def research_roadmap(canvas, number, evidence):
    page = Page(canvas, number, "Research / the larger programme")
    page.heading("Twenty scenarios.<br/>One staged research programme.", size=40)
    page.paragraph(
        "We planned a progression of hypotheses about extraction: introduce a "
        "specific difficulty, diagnose the failure, then test an improvement. "
        "Within the hackathon window, we established the <b>baseline and a "
        "constrained alias resolver</b>. The wider programme remains ahead.",
        48, 193, 624, 16, 23)
    page.text("Planned challenges, in increasing complexity", 48, 319, 19, FOREST, "SansBold")
    page.paragraph("01–05 have authored development cases. 06–20 are planned scenarios, not validated capabilities.",
                   48, 353, 624, 12, 17, MUTED)
    challenges = [
        "Explicit family / Trust facts", "Dense facts and overlapping roles",
        "Aliases for the same person", "Cross-document reconciliation",
        "Changed relationships", "Contradictory Sources",
        "Ambiguous role attribution", "Indirect relationship descriptions",
        "Negation and hypothetical claims", "Larger, denser family graphs",
        "Multiple Trusts", "Corporate / non-person trustees",
        "Different document genres", "Locally resolvable pronouns",
        "Sibling / cousin distinction", "Overlapping Evidence spans",
        "Longer Sources and distractors", "Unnamed participants / omission",
        "Historical versus current state", "Combined stress test",
    ]
    for index, label in enumerate(challenges):
        x = 48 if index < 10 else 372
        y = 402 + (index % 10) * 32
        page.text(f"{index+1:02d}", x, y, 12, FOREST if index < 5 else MUTED,
                  "SansBold" if index < 5 else "Sans")
        page.text(label, x+29, y, 12.5, INK)
    page.line(48, 735, 672, 735)
    page.paragraph(
        "<b>20 roadmap scenarios · 5 authored development cases · 10 separate held-out cases.</b> "
        "These are different scopes. The held-out study evaluates the baseline-plus-resolver "
        "slice; it does not complete the twenty-scenario roadmap.",
        48, 758, 624, 14, 20)
    page.footer("Case progression: cases/README.md. Scenario labels condensed for this document.", ROADMAP)


def benchmark_design(canvas, number, evidence):
    page = Page(canvas, number, "Research / benchmark construction")
    page.heading("A small benchmark,<br/>with an explicit boundary", size=43)
    page.paragraph(
        "The first five roadmap scenarios supplied development cases. A separate held-out set tested "
        "whether those choices carried into new documentary situations. All cases "
        "were authored for this project and contain synthetic information.",
        48, 199, 624)
    benchmark = evidence["benchmark"]
    for x, value, label in ((48, benchmark["case_count"], "held-out cases"),
                            (260, benchmark["source_count"], "Sources"),
                            (472, benchmark["expected_relationships"], "expected relationships")):
        page.text(str(value), x, 316, 58, FOREST, "Serif")
        page.text(label, x, 384, 13, MUTED)
    page.line(48, 424, 672, 424)
    page.text("What the held-out cases ask", 48, 447, 21, INK, "Serif")
    examples = (("heldout_02", "Dense wording", "Separate sibling status from beneficiary roles."),
                ("heldout_05", "A completed replacement", "Retain earlier facts; remove the superseded trustee."),
                ("heldout_08", "Matching document titles", "Preserve distinct Source identities."))
    for index, (case_id, label, question) in enumerate(examples):
        top = 492 + index * 65
        page.text(case_id.replace("heldout_", "Held-out "), 48, top, 11.5, MUTED)
        page.text(label, 140, top - 1, 15, FOREST, "SansBold")
        page.paragraph(question, 140, top + 22, 532, 14, 20)
    page.paragraph(
        "<b>Ground truth was checked separately from authoring by AI validators.</b> "
        "These were internal checks, not external human or institutional validation. "
        "The retained comparison freezes its inputs and records its outcomes; it "
        "does not turn this small synthetic set into evidence of field performance.",
        48, 714, 624, 15, 22)
    page.footer("Benchmark counts: retained publication; independent AI checks: validation records.", VALIDATION)


def measurement(canvas, number, evidence):
    page = Page(canvas, number, "Research / what the scores mean")
    page.heading("Count the relationships.<br/>Then check the Evidence.", size=43)
    page.paragraph(
        "The primary score compares exact relationship edges: the named starting "
        "entity, relationship type and named target entity. Direction matters for directed links; "
        "symmetric links are canonicalised. A plausible sentence alone is not a match.",
        48, 198, 624)
    page.rect(48, 319, 624, 102, CHALK)
    page.text("F1 = 2 × TP / (2 × TP + FP + FN)", 70, 342, 24, FOREST, "Serif")
    page.paragraph("TP: matched edges · FP: extra edges · FN: missing edges", 70, 384, 580, 13, 18)
    baseline = _run(evidence, "A")["metrics"]
    page.text("Two valid averages answer different questions", 48, 457, 22, INK, "Serif")
    page.text(f'{baseline["micro_f1"]:.2%}', 48, 505, 35, BURGUNDY, "Serif")
    page.paragraph("<b>Micro-F1, baseline A.</b> Pool edge counts across all cases. "
                   "Cases with more relationships contribute more edges.",
                   240, 503, 432, 15, 22)
    page.text(f'{baseline["macro_f1"]:.2%}', 48, 595, 35, BURGUNDY, "Serif")
    page.paragraph("<b>Macro-F1, baseline A.</b> Average the ten case F1 scores. "
                   "Each case contributes equally, whatever its size.",
                   240, 592, 432, 15, 22)
    page.line(48, 676, 672, 676)
    page.paragraph(
        "<b>Provenance is assessed separately.</b> Approved-quote checks concern "
        "matched relationships; Source/quote-pair checks concern evidence pairs. "
        "Their populations differ, and neither score should be read as another "
        "relationship-accuracy percentage.", 48, 707, 624, 16, 23)
    page.footer("Definitions: semantic_edges_v1; separate approved-provenance diagnostics.", PUBLICATION)


def alias_correction(canvas, number, evidence):
    page = Page(canvas, number, "Research / anatomy of the correction")
    page.heading("One person.<br/>Two corrected endpoints.", size=43)
    case = _case(evidence, "heldout_03")
    source = case["sources"][0]
    # The published source retains escaped newlines; display only its exact sentence.
    text = source["text"].replace("\\n", "\n")
    introduction = text.split("\n\n")[1]
    page.text("Heldout_03: factual interview note", 48, 201, 11.5, MUTED, "SansBold")
    page.rect(48, 237, 624, 148, YELLOW)
    page.paragraph("“" + escape(introduction) + "”", 70, 259, 580, 25, 31, INK, "Serif")
    page.paragraph("Exact Source excerpt from the synthetic held-out case. Editorial figure.",
                   48, 399, 624, 11.5, 16, MUTED)
    edits = _observation(case, "B")["edits"]
    page.text("Endpoint correction", 48, 434, 10.5, MUTED)
    page.text("Unchanged target", 372, 434, 10.5, MUTED)
    for index, edit in enumerate(edits):
        y = 453 + index * 104
        page.text(edit["relationship_type"].replace("_", " ").capitalize(), 48, y, 13, MUTED, "SansBold")
        page.text(edit["original_name"], 48, y + 28, 24, BURGUNDY, "Serif")
        page.line(102, y + 42, 154, y + 42, FOREST, 1)
        page.line(149, y + 38, 154, y + 42, FOREST, 1)
        page.line(149, y + 46, 154, y + 42, FOREST, 1)
        page.text(edit["resolved_name"], 174, y + 28, 24, FOREST, "Serif")
        page.text(edit["other_endpoint"], 372, y + 33, 16, INK)
        page.paragraph("“" + escape(edit["supporting_text"]) + "”", 48, y + 66, 624, 15, 21, INK, "Serif")
    page.paragraph("The already-correct Isaac Ng beneficiary relationship remains unchanged.",
                   48, 665, 624, 13, 18)
    page.line(48, 703, 672, 703)
    page.paragraph(
        "<b>The resolver returns endpoint-name edits only.</b> Code preserves "
        "candidate count, relationship types, directions and quotations. Replacement "
        "names must occur in the Sources or extracted endpoints. Whether two names "
        "identify the same person remains a model judgment.",
        48, 725, 624, 14, 20)
    page.footer("Retained heldout_03 Source, endpoint edits and relationship observations.", PUBLICATION)


def case_results(canvas, number, evidence):
    page = Page(canvas, number, "Research / case-level results")
    page.heading("Nine cases already had<br/>perfect relationship F1", size=43)
    page.paragraph(
        "Every case except the explicit Bea short form scored 100% relationship F1 "
        "before resolution and after it. This locates the gain precisely; it does "
        "not demonstrate a broad improvement across ten distinct failures.",
        48, 197, 624)
    page.text("Relationship F1 per case", 48, 297, 13, INK, "SansBold")
    page.circle(437, 303, 3.5, BURGUNDY)
    page.text("A / A′", 448, 297, 11.5, MUTED)
    page.circle(534, 303, 3.5, FOREST)
    page.text("B", 545, 297, 11.5, MUTED)
    x0, chart_width = 477, 180
    for value in (0, 0.5, 1):
        x = x0 + value * chart_width
        page.text(f"{value:.0%}", x, 332, 10.5, MUTED, align="center")
        page.line(x, 352, x, 739, CHALK, 1)
    for index, case in enumerate(evidence["cases"]):
        y = 362 + index * 38
        a = _observation(case, "A")["evaluation"]["f1"]
        b = _observation(case, "B")["evaluation"]["f1"]
        page.text(case["case_id"].replace("heldout_", ""), 48, y, 11.5, MUTED)
        page.paragraph(escape(case["name"]), 82, y - 2, 373, 12, 15, max_height=32)
        page.line(x0 + a * chart_width, y + 12, x0 + b * chart_width, y + 12, MUTED, 1)
        page.circle(x0 + a * chart_width, y + 7, 3.5, BURGUNDY)
        page.circle(x0 + b * chart_width, y + 17, 3.5, FOREST)
    changed = _case(evidence, "heldout_03")
    before = _observation(changed, "A")["evaluation"]["f1"]
    after = _observation(changed, "B")["evaluation"]["f1"]
    page.paragraph(
        f"<b>Case 03: {before:.2%} to {after:.0%}.</b> Points use the full 0–100% scale. "
        "The paired markers are separated vertically so equal scores remain visible. "
        "A′ exactly reproduces A. One execution per case; no repeated-trial uncertainty estimate.",
        48, 767, 624, 13, 18)
    page.footer("Case names and plotted F1 values: retained publication. Editorial chart.", PUBLICATION)


def evidence_and_cost(canvas, number, evidence):
    page = Page(canvas, number, "Research / remaining evidence gaps and usage")
    page.heading("Perfect edges do not<br/>mean perfect Evidence", size=43)
    run = _run(evidence, "B")
    metrics, usage = run["metrics"], run["usage"]
    page.paragraph(
        f'B passed <b>{metrics["quote_passed"]}/{metrics["quote_assessed"]} approved-quote checks</b> '
        f'and <b>{metrics["source_pair_passed"]}/{metrics["source_pair_assessed"]} Source/quote-pair checks</b>. '
        "These are separate populations. Exact approved boundaries can fail even "
        "when a shorter quotation supports the relationship.", 48, 198, 624)
    case = _case(evidence, "heldout_02")
    relationship = next(r for r in _observation(case, "B")["relationships"]
                        if r["edge"] == ["Grace Wong", "sibling_of", "Hugo Wong"])
    page.text("Case 02: Grace Wong is a sibling of Hugo Wong", 48, 320, 11.5, MUTED, "SansBold")
    page.rect(48, 354, 624, 212, CHALK)
    page.text("Approved span", 68, 371, 11.5, MUTED, "SansBold")
    page.paragraph("“" + escape(relationship["expected"][0]["text"]) + "”",
                   68, 394, 584, 17, 22, INK, "Serif")
    page.text("Returned span · same Source, later start boundary", 68, 477, 11.5, MUTED, "SansBold")
    page.paragraph("“" + escape(relationship["predicted"][0]["text"]) + "”",
                   68, 501, 584, 17, 22, INK, "Serif")
    page.paragraph("Exact retained excerpts. This mismatch does not imply an unsupported sibling claim.",
                   48, 579, 624, 11.5, 16, MUTED)
    page.line(48, 621, 672, 621)
    page.text("The incremental resolver usage", 48, 644, 23, INK, "Serif")
    page.paragraph(
        f'<b>{usage["attempts"]} calls · {usage["total_tokens"]:,} tokens</b><br/>'
        f'{usage["input_tokens"]:,} input + {usage["output_tokens"]:,} output. '
        f'The {usage["cached_tokens"]:,} cached input tokens are included, not additional. '
        "USD cost is unpriced in the retained record.", 48, 685, 624, 16, 23)
    model = run["calls"][0]["model"]
    page.paragraph(
        f"All calls use {escape(model)}. This post-hoc comparison uses one provider/model "
        "and one execution per case; it supplies no repeated-trial estimate of stability "
        "or end-to-end latency claim.", 48, 778, 624, 12, 17)
    page.footer("Exact approved / predicted spans and incremental B usage: retained publication.", PUBLICATION)


def _run(evidence, label):
    return next(run for run in evidence["runs"] if run["label"] == label)


def _case(evidence, case_id):
    return next(case for case in evidence["cases"] if case["case_id"] == case_id)


def _observation(case, label):
    return next(observation for observation in case["observations"]
                if observation["run_label"] == label)
