"""Architecture, interpretation and closing pages of the judge folio."""

from layout import CHALK, FOREST, MUTED, WHITE, Page
from pages import GITHUB, PRODUCTION, PUBLICATION

PIN = GITHUB + "/blob/d5130917b32ba03e41d6345a8c3d604f4c906432/"


def architecture(canvas, number, evidence):
    page = Page(canvas, number, "System design", dark=True)
    page.heading("AI interprets.<br/>Code enforces the rules.",
                 y=83, size=42, color=WHITE)
    page.paragraph(
        "Language requires interpretation. Graph integrity should not depend on "
        "another guess. PCG assigns those jobs to different parts of one fixed "
        "Extract / Resolve / Construct pipeline.",
        48, 202, 624, 16, 23, WHITE)

    page.line(72, 327, 72, 592, WHITE, 1)
    stages = [
        (312, "Extract relationships", "Model",
         "Read the ordered Sources together. Propose relationship candidates "
         "with named endpoints and Source-attributed quotations."),
        (425, "Resolve names", "Configuration choice",
         "Application intake currently uses no resolution. Research can add a "
         "constrained model stage to correct supported endpoint names."),
        (538, "Construct the graph", "Deterministic code",
         "Validate types, references and exact quote occurrence. Assign stable "
         "identities, pool Evidence and produce canonical graph structure."),
    ]
    for top, title, owner, explanation in stages:
        page.circle(72, top+15, 7, WHITE)
        page.text(title, 104, top, 23, WHITE, "SansBold")
        page.text(owner, 104, top+34, 11.5, WHITE)
        page.paragraph(explanation, 104, top+57, 552, 14, 20, WHITE)

    page.rect(48, 694, 624, 119, CHALK)
    page.text("Mechanical validity is only one boundary", 67, 713, 18, FOREST, "SansBold")
    page.paragraph(
        "Code can establish that a quotation occurs in a Source. That does not "
        "prove it supports the relationship. Professional acceptance remains "
        "explicit; deterministic benchmark evaluation runs separately.",
        67, 747, 585, 14, 20)
    page.footer("Architecture: ADRs 0001 and 0009; current application configuration.",
                PIN + "docs/adr/0009-share-one-fixed-configurable-analysis-pipeline.md")


def interpretation(canvas, number, evidence):
    page = Page(canvas, number, "Interpretation and reproducibility")
    page.heading("A useful finding.<br/>A defined boundary.", y=83, size=43)
    page.paragraph(
        "The experiment demonstrates a traceable correction under controlled "
        "inputs. It also shows why an attractive graph and a high relationship "
        "score must remain open to inspection.",
        48, 197, 624, 16, 23)

    page.text("What the record supports", 48, 300, 21, FOREST, "SansBold")
    page.paragraph(
        "The resolver repaired the two observed endpoint names without changing "
        "the other nine cases' relationship outcomes. The retained examples also "
        "include multi-source corroboration, identical Source titles and explicit "
        "trustee replacement. These are observations within this dataset.",
        48, 341, 624, 15, 22)

    page.text("What it cannot establish", 48, 463, 21, FOREST, "SansBold")
    page.paragraph(
        "Ten short, project-authored synthetic cases are not a representative "
        "client-document collection. The study used one model, deepseek-flash, "
        "with one extraction and one resolver execution per case. There were no "
        "repeated trials or uncertainty estimates. The comparison was post-hoc; "
        "general identity resolution and real-document reliability remain untested.",
        48, 504, 624, 15, 22)

    page.rect(48, 654, 624, 162, CHALK)
    page.text("An inspectable record, not a fresh model promise", 66, 674, 18, FOREST, "SansBold")
    page.paragraph(
        "Frozen Sources, settings, code identities, outputs, checksums and usage "
        "preserve the comparison. Replaying saved outputs reproduces the record, "
        "not a fresh model response. Workbench approval binds a frozen plan to a "
        "shared call budget; uncertain attempts remain counted and are not "
        "automatically retried.",
        66, 711, 585, 14, 20)
    page.footer("Retained observations, limitations and publication verification.", PUBLICATION)


def future_direction(canvas, number, evidence):
    page = Page(canvas, number, "Next development decisions")
    page.heading("The next version needs<br/>new evidence", y=83, size=43)
    page.paragraph(
        "The hackathon established baseline extraction and a constrained resolver. "
        "Continue the twenty-scenario programme by isolating new failure modes "
        "and testing improvements, alongside the product work below.",
        48, 197, 624, 16, 23)

    rows = [
        (301, "Validate the review workflow",
         "Observe practitioners finding missing claims, checking Evidence and "
         "deciding whether to accept a proposal. Test the Trust layout and "
         "measure task outcomes before claiming time savings or usability."),
        (443, "Support change over time",
         "Design incremental Matter updates, reviewed changes, corrections and "
         "historical state. A narrow trustee-replacement example does not yet "
         "provide a general temporal or contradiction-handling system."),
        (585, "Design the real-data boundary",
         "Develop Matter authorization, tenancy and ownership, and explicit "
         "security, privacy, retention and data-handling requirements. Current "
         "sign-in and allowlisted actions do not authorize real client material."),
    ]
    for top, title, body in rows:
        page.line(48, top-16, 672, top-16)
        page.text(title, 48, top, 22, FOREST, "SansBold")
        page.paragraph(body, 48, top+40, 624, 15, 22)

    page.paragraph(
        "Research should use newly unseen cases, richer documents and repeated "
        "runs. The published held-out set is now visible and must not be treated "
        "as unseen evidence in subsequent work informed by it.",
        48, 742, 624, 14, 21, MUTED)
    page.footer("Proposed future work; not delivered capability or an adoption claim.",
                PIN + "PRODUCT.md")


def closing_references(canvas, number, evidence):
    page = Page(canvas, number, "Explore the evidence")
    page.heading("Make every relationship<br/>reviewable", y=83, size=43)
    page.paragraph(
        "Private Client Graph combines a tangible practitioner workflow, explicit "
        "professional acceptance and a research record that can be inspected "
        "down to the original words. That is the foundation worth developing: "
        "AI-assisted structure whose claims remain open to challenge. The baseline "
        "and resolver are the first tested slice of a twenty-scenario research roadmap.",
        48, 197, 624, 16, 23)

    page.text("Open the prototype", 48, 340, 18, FOREST, "SansBold")
    page.link("private-client-graph-production.up.railway.app", PRODUCTION + "/",
              48, 371, 13, FOREST)
    page.text("Inspect the retained research", 48, 399, 18, FOREST, "SansBold")
    page.link("Research results and downloadable original publication",
              PRODUCTION + "/research-results", 48, 430, 13, FOREST)
    page.text("Read the implementation", 48, 472, 18, FOREST, "SansBold")
    page.link("github.com/alistairkung/private-client-graph", GITHUB,
              48, 503, 13, FOREST)

    page.line(48, 546, 672, 546)
    page.text("Sources and visual provenance", 48, 566, 19, FOREST, "SansBold")
    references = [
        ("Product and architecture", "README, glossary and ADRs 0001, 0005, 0006, 0009-0011.",
         PIN + "README.md"),
        ("Benchmark and retained results", "Held-out cases, validator reports and the frozen A / A′ / B publication.",
         PUBLICATION),
        ("Product images", "PR #160 current UI; PR #155 historical workflow captures. Synthetic fixtures; model substituted.",
         PIN + "docs/artifacts/ui-consolidation/README.md"),
        ("Research chart and editorial figures", "Actual production chart captured 18 Oct 2026. Other diagrams explain recorded facts.",
         PRODUCTION + "/research-results#comparison"),
    ]
    for index, (label, description, url) in enumerate(references):
        top = 603 + index*47
        page.link(label, url, 48, top, 11.5, FOREST)
        page.paragraph(description, 48, top+18, 624, 10.5, 14, MUTED)
    page.text("Synthetic-data prototype. Not validated for real client use.", 48, 814,
              12, FOREST, "SansBold")
    page.footer("Links and current product inspected on 18 October 2026.", PRODUCTION + "/")
