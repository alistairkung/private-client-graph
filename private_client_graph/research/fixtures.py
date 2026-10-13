"""Load the six reviewed development inputs; missing evidence is an error."""
import hashlib
import json
from pathlib import Path

from .inputs import ResearchInput

ROOT = Path(__file__).resolve().parents[2]


def load_inputs(root: Path = ROOT) -> list[ResearchInput]:
    fixtures = root / "research" / "fixtures"
    samples = []
    for case in ("case_01", "case_02", "case_03"):
        samples.append(_load(
            root / "cases" / case, f"{case}_fixture", case,
            fixtures / f"{case}_annotations.json", "expected_extraction.json",
        ))
    history = fixtures / "case_03_historical"
    metadata = json.loads((history / "metadata.json").read_text())
    sample = _load(root / "cases" / "case_03", "case_03_historical", "case_03",
                   fixtures / "case_03_annotations.json", history / "extraction.json")
    for filename, expected in metadata["file_sha256"].items():
        if sample.origin_hashes[filename] != expected:
            raise ValueError("Historical fixture hash mismatch")
    sample.cohort = "historical"
    sample.historical = {"metadata": metadata,
                         "raw_extraction": (history / "extraction.json").read_text(),
                         "raw_metadata": (history / "metadata.json").read_text()}
    samples.append(sample)
    for name in ("alias_merge", "alias_distinct"):
        samples.append(_load(fixtures / name, name, name,
                             fixtures / name / "annotations.json", "extraction.json"))
    return samples


def _load(directory: Path, sample_id: str, case_id: str,
          annotations: Path, extraction_path: str | Path) -> ResearchInput:
    paths = {"source.txt": directory / "source.txt",
             "ground_truth.json": directory / "ground_truth.json",
             "extraction.json": directory / extraction_path,
             "annotations.json": annotations}
    raw = {name: path.read_bytes() for name, path in paths.items()}
    return ResearchInput(
        sample_id=sample_id, case_id=case_id, cohort="authored",
        source=raw["source.txt"].decode(), truth=json.loads(raw["ground_truth.json"]),
        extraction=json.loads(raw["extraction.json"]),
        annotations=json.loads(raw["annotations.json"]),
        origin_hashes={name: hashlib.sha256(value).hexdigest() for name, value in raw.items()},
    )
