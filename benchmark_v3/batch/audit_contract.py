"""Scope scientific audit findings to the frozen maps."""

from typing import Any

from benchmark_v3.batch.contracts import AuditReview
from benchmark_v3.commissioning import json_text
from benchmark_v3.replay_manifest import BatchSourceFreeze
from private_client_graph.models.source import Source

SCOPED_INSTRUCTIONS = (
    " In sufficiency, use only the frozen required edge keys listed in the schema. "
    "Record all whole-graph observations, including evidence for other adjudicated relationships, "
    "in the applicable per-Source completeness findings. Check for missing supported claims and "
    "included unsupported claims. Use negative_controls for unsupported candidate relationships "
    "and shortcuts for misleading routes. Independently assess every approved evidence route, "
    "including joint alternatives outside the critical map. Record material concerns in objections. "
    "Precommit the independent observations needed to test those routes; the observations follow this audit."
)


def output_schema(bundles: dict[str, list[Source]], freeze: BatchSourceFreeze) -> dict[str, Any]:
    schema = AuditReview.model_json_schema()
    finding = {"type": "string", "minLength": 1}
    schema["properties"]["completeness"] = _exact_object({
        condition: _exact_object({source.id: finding for source in sources})
        for condition, sources in bundles.items()
    })
    schema["properties"]["sufficiency"] = _exact_object({
        condition: _exact_object({json_text(edge): finding for edge in freeze.required[condition]})
        for condition in bundles
    })
    return schema


def _exact_object(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }
