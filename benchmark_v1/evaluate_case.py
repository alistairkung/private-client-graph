"""Reproduce legacy graph and approved-quotation scores for a single-text fixture."""

import argparse
import json
from pathlib import Path

from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import build_graph
from private_client_graph.models import ExtractionResult, GroundTruth


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path, help="Directory containing source.txt and ground_truth.json")
    parser.add_argument("run", type=Path, help="Legacy ExtractionResult JSON")
    parser.add_argument("--output", type=Path, help="New output path (defaults to RUN.evaluation.json)")
    args = parser.parse_args()

    payload = json.loads(args.run.read_bytes())
    extraction = ExtractionResult.model_validate(payload)
    if any("source_id" in row for row in payload["relationships"]):
        parser.error("Use the Research Workbench for Source-attributed replay and diagnostics.")

    source = args.case_dir / "source.txt"
    graph = build_graph(extraction.relationships, document=source.as_posix(),
                        source_text=source.read_text(encoding="utf-8"))
    truth = GroundTruth.model_validate_json((args.case_dir / "ground_truth.json").read_bytes())
    output = evaluate_graph(graph, truth).model_dump_json(indent=2)
    destination = args.output or args.run.with_suffix(".evaluation.json")
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(output + "\n")
    print(output)


if __name__ == "__main__":
    main()
