"""Score completed offline replays. Run with python -m research.discovery.evaluate."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .replay import CORPUS_SHA256, LIMITS, QUERY, SCOPE, replay


def fraction(numerator: int, denominator: int) -> dict:
    return {"numerator": numerator, "denominator": denominator,
            "value": numerator / denominator if denominator else None}


def score(run: dict, labels: dict) -> dict:
    relevant = set(labels["relevant"])
    eligible = relevant | set(labels["irrelevant"])
    for point in run["checkpoints"]:
        surfaced = set(point["surfaced"])
        if not surfaced <= eligible:
            raise ValueError(f"Excluded or unlabelled candidates surfaced: {sorted(surfaced - eligible)}")
        correct = len(relevant & surfaced)
        point["recall"] = fraction(correct, len(relevant))
        point["precision"] = fraction(correct, len(surfaced))
        point["irrelevant_hits"] = sorted(surfaced - relevant)
        read = set(point["original_inspected"]) | set(point["opened_emails"])
        point["unread_email_hits"] = sorted(key for key in surfaced if key.startswith("email:")
                                             and key.removeprefix("email:") not in read)
    for approval in run["approvals"]:
        if set(approval["hits"]) & relevant:
            approval["false_lead"] = False
        elif approval["stop_reason"] or approval["more_pages"]:
            approval["false_lead"] = None
        else:
            approval["false_lead"] = True
    return run


def evaluate(*, timing: bool = False) -> dict:
    arms = {
        variant: {arm: replay(expand=expand, alternate=alternate, timing=timing)
                  for arm, expand in (("original", False), ("expanded", True))}
        for variant, alternate in (("primary", False), ("paired", True))
    }
    labels = json.loads(Path(__file__).with_name("labels.json").read_text())
    return {
        "fixture": "alder-trust-v1", "corpus_sha256": CORPUS_SHA256,
        "scope": asdict(SCOPE), "query": QUERY, "limits": asdict(LIMITS),
        "ranking": "outstanding-document rules, appointment first, top three",
        "discovery_model_calls": 0, "discovery_model_tokens": 0, "human_walkthrough_seconds": None,
        "arms": {variant: {arm: score(run, labels) for arm, run in runs.items()}
                 for variant, runs in arms.items()},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timing", action="store_true", help="include machine-dependent offline replay times")
    print(json.dumps(evaluate(timing=parser.parse_args().timing), indent=2))
