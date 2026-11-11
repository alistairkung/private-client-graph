"""Evaluate a saved extraction run against any benchmark case.

Usage:
    uv run python benchmark_v1/evaluate_case.py <case_dir> <run.json>

Example:
    uv run python benchmark_v1/evaluate_case.py \
        benchmark_v1/aliases/dev/case_1 \
        benchmark_v1/aliases/dev/case_1/runs/2026-11-11T140000.json
"""

import argparse
from pathlib import Path

from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import build_graph
from private_client_graph.models import ExtractionResult, GroundTruth


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path, help="Case folder containing source.txt and ground_truth.json")
    parser.add_argument("run", type=Path, help="Saved extraction JSON")
    args = parser.parse_args()

    # Load the extraction
    extraction = ExtractionResult.model_validate_json(
        args.run.read_text(encoding="utf-8")
    )

    # Load the case's source and ground truth (NOT hardcoded to Case 01)
    source_path = args.case_dir / "source.txt"
    ground_truth_path = args.case_dir / "ground_truth.json"

    graph = build_graph(
        extraction.relationships,
        document=source_path.as_posix(),
        source_text=source_path.read_text(encoding="utf-8"),
    )

    ground_truth = GroundTruth.model_validate_json(
        ground_truth_path.read_text(encoding="utf-8")
    )

    result = evaluate_graph(graph, ground_truth)
    output = result.model_dump_json(indent=2)
    output_path = args.run.with_suffix(".evaluation.json")

    # 'x' mode fails if file exists — prevents accidental overwrites
    with output_path.open("x", encoding="utf-8") as output_file:
        output_file.write(output + "\n")

    print(output)


if __name__ == "__main__":
    main()