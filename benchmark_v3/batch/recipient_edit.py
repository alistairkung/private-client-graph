"""Derive a strictly local documentary amendment from an earlier owned Source."""

from collections.abc import Sequence
from typing import Self

from pydantic import model_validator

from benchmark_v3.batch.contracts import DesignOutput, SourceId
from benchmark_v3.research_contracts import Contract, Digest, Text
from private_client_graph.models.source import Source


class ExactRecipientEdit(Contract):
    source_id: SourceId
    brief_omission: Text | None = None
    omitted_paragraph: Text | None = None
    old_label: Text
    new_label: Text
    feasibility_sha256: Digest

    @model_validator(mode="after")
    def _verify_omission_pair(self) -> Self:
        if (self.brief_omission is None) != (self.omitted_paragraph is None):
            raise ValueError("A documentary omission requires the two corresponding exact spans.")
        return self

    def require_exact_omission_objections(self, objections: Sequence[str]) -> None:
        if (self.brief_omission is None or self.omitted_paragraph is None
                or len(objections) != 2 or any(self.source_id not in message for message in objections)
                or sum(self.brief_omission in message for message in objections) != 1
                or sum(self.omitted_paragraph in message for message in objections) != 1):
            raise ValueError("This recheck requires the two exact objections to the local omissions.")

    def revise_design(self, design: DesignOutput) -> DesignOutput:
        row = next(item for item in design.inventory if item.source_id == self.source_id)
        if self.brief_omission is None:
            return design
        text = row.participant_brief
        if text.count(self.brief_omission) != 1:
            raise ValueError("The old participant instruction must contain the exact unsupported summary once.")
        revised = row.model_copy(update={"participant_brief": text.replace(self.brief_omission + " ", "", 1)})
        if revised == row:
            raise ValueError("The participant instruction must support one exact sentence-level removal.")
        return design.model_copy(update={"inventory": [revised if item.source_id == self.source_id else item
                                                        for item in design.inventory]})

    def revise_source(self, previous: Source) -> Source:
        paragraph = f"\n\n{self.omitted_paragraph}\n\n" if self.omitted_paragraph is not None else None
        if (previous.id != self.source_id or (paragraph is not None and previous.text.count(paragraph) != 1)
                or previous.text.count(self.old_label) != 1 or self.old_label == self.new_label
                or any("\n" in item or "\r" in item for item in (self.old_label, self.new_label))):
            raise ValueError("A retained recipient repair needs one exact paragraph and one ordinary label.")
        retained = previous.text if paragraph is None else previous.text.replace(paragraph, "\n\n", 1)
        corrected = retained.replace(self.old_label, self.new_label, 1)
        return previous.model_copy(update={"text": corrected})
