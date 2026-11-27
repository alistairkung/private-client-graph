"""Keep separately addressed native documents out of a shared attachment."""

import re

from pydantic import TypeAdapter

from benchmark_v3 import commissioning
from benchmark_v3.batch.contracts import DesignOutput
from private_client_graph.models.source import Source


HALT = "An atomic Source combined mutually restricted recipient messages in a dispatched author packet."
_SEPARATE_VERSIONS = re.compile(
    r"(?:each recipient\b[^.\n]{0,90}\bonly\b[^.\n]{0,90}\b(?:message|version|letter|email)\b"
    r"|(?:issued|sent|addressed|delivered)\s+(?:in\s+)?separate\s+(?:messages|versions|letters|emails)\b"
    r"|separately\s+(?:addressed|issued|sent)\s+(?:messages|versions|letters|emails)\b)", re.IGNORECASE,
)
_HEADER = re.compile(r"^\s*[#>*\[\-` ]*(?:(?:draft|message|e-?mail|letter)\s+)?to\s*:\s*([^\r\n]+)",
                     re.IGNORECASE | re.MULTILINE)


class AudienceError(ValueError):
    """A candidate cannot dispatch an atomic record with incompatible audiences."""


def verify_design(design: DesignOutput) -> None:
    attachments = {identity for row in design.inventory for identity in row.received}
    for row in design.inventory:
        if row.source_id in attachments and _SEPARATE_VERSIONS.search(f"{row.provenance}\n{row.participant_brief}"):
            raise AudienceError(
                f"Attachment {row.source_id} packages separately issued messages. Use one authenticated Source per restricted audience.",
            )


def verify_packet(inputs: dict[str, str]) -> None:
    """Verify the actual serialized attachment, including headings inside the documentary body."""
    attachments = TypeAdapter(list[Source]).validate_json(inputs["received_correspondence"])
    for source in attachments:
        participants = {tuple(re.findall(r"\w+", match.casefold())) for match in _HEADER.findall(source.text)}
        if len(participants) > 1 or _SEPARATE_VERSIONS.search(source.text):
            raise AudienceError(
                f"Attachment {source.id} contains documents with different recipient headings or declared separate audiences.",
            )
