"""Evaluate a saved Case 01 extraction run from the repository root."""

import argparse
from pathlib import Path

from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import build_graph
from private_client_graph.models import ExtractionResult, GroundTruth


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="saved Case 01 extraction JSON")
    args = parser.parse_args()

    extraction = ExtractionResult.model_validate_json(args.run.read_text(encoding="utf-8"))
    source_path = Path("cases/case_01/source.txt")
    graph = build_graph(
        extraction.relationships,
        document=source_path.as_posix(),
        source_text=source_path.read_text(encoding="utf-8"),
    )
    ground_truth = GroundTruth.model_validate_json(
        Path("cases/case_01/ground_truth.json").read_text(encoding="utf-8")
    )
    result = evaluate_graph(graph, ground_truth)
    output = result.model_dump_json(indent=2)
    output_path = args.run.with_suffix(".evaluation.json")
    with output_path.open("x", encoding="utf-8") as output_file:
        output_file.write(output + "\n")
    print(output)


if __name__ == "__main__":
    main()
