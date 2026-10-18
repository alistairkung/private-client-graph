"""Render the judge folio or its approved sample from frozen local sources."""

import argparse
import json
from pathlib import Path

from reportlab.pdfgen.canvas import Canvas

from layout import HEIGHT, ROOT, WIDTH, register_fonts
from localization import translate
from pages import SAMPLE_PAGES, cover, measured_results, paired_experiment, product_inspection
from product_pages import (distinct_claims, multiple_sources, original_problem,
                           professional_acceptance, synthetic_intake)
from research_pages import (alias_correction, benchmark_design, case_results,
                            evidence_and_cost, measurement, research_method, research_roadmap)
from editorial_pages import architecture, closing_references, future_direction, interpretation


FULL_PAGES = [
    ("From documents to reviewable relationships", cover),
    ("The original problem", original_problem),
    ("Family facts and Trust roles", distinct_claims),
    ("A graph you can question", product_inspection),
    ("Synthetic multi-PDF intake", synthetic_intake),
    ("Professional acceptance", professional_acceptance),
    ("More than one Source", multiple_sources),
    ("The semantic and deterministic boundary", architecture),
    ("The case-led development method", research_method),
    ("Benchmark construction", benchmark_design),
    ("What the scores mean", measurement),
    ("The controlled comparison", paired_experiment),
    ("The two endpoint corrections", alias_correction),
    ("Recorded aggregate findings", measured_results),
    ("Every case result", case_results),
    ("Evidence gaps and resolver usage", evidence_and_cost),
    ("Interpretation and reproducibility", interpretation),
    ("Next development decisions", future_direction),
    ("The twenty-scenario research roadmap", research_roadmap),
    ("Explore the evidence and sources", closing_references),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="store_true",
                        help="Build the four representative pages for the creative checkpoint.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--english-only", action="store_true",
                        help="Render only the English edition for editorial review.")
    args = parser.parse_args()
    evidence = json.loads((ROOT / "private_client_graph/published/research-results.v1.json").read_text())
    pages = [(function.__name__.replace("_", " "), function) for function in SAMPLE_PAGES] if args.sample else FULL_PAGES
    filename = "private-client-graph-creative-sample.pdf" if args.sample else "private-client-graph-judge-folio.pdf"
    output = args.output or ROOT / "output/pdf" / filename
    register_fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output), pagesize=(WIDTH, HEIGHT), pageCompression=1,
                    invariant=1)
    canvas.setTitle("Private Client Graph - " + ("Creative sample" if args.sample else "From documents to reviewable relationships"))
    canvas.setAuthor("Private Client Graph")
    canvas.setCreator("Private Client Graph editorial build")
    canvas.setSubject("FTEC5660 Private Wealth; English then Simplified Chinese; synthetic-data prototype")
    languages = ["en"] if args.sample or args.english_only else ["en", "zh"]
    for edition, language in enumerate(languages):
        canvas.folio_language = language
        canvas.bookmarkPage(language)
        canvas.addOutlineEntry("English" if language == "en" else "简体中文", language)
        for index, (title, page) in enumerate(pages, start=1):
            number = edition*len(pages) + index
            bookmark = f"{language}-{index}"
            canvas.bookmarkPage(bookmark)
            canvas.addOutlineEntry(translate(title, language), bookmark, level=1)
            page(canvas, number, evidence)
    canvas.showOutline()
    canvas.save()
    size = output.stat().st_size
    if size >= 20_000_000:
        raise ValueError(f"PDF exceeds the strict submission limit: {size} bytes")
    print(json.dumps({"path": str(output), "pages": len(pages)*len(languages), "bytes": size}))


if __name__ == "__main__":
    main()
