"""Derive a strictly local documentary amendment from an earlier owned Source."""

from benchmark_v3.batch.contracts import DesignOutput, SourceId
from benchmark_v3.research_contracts import Contract, Digest, Text
from private_client_graph.models.source import Source


class ExactRecipientEdit(Contract):
    source_id: SourceId
    brief_omission: Text
    omitted_paragraph: Text
    old_label: Text
    new_label: Text
    feasibility_sha256: Digest

    def revise_design(self, design: DesignOutput) -> DesignOutput:
        row = next(item for item in design.inventory if item.source_id == self.source_id)
        text = row.participant_brief
        if text.count(self.brief_omission) != 1:
            raise ValueError("The old participant instruction must contain the exact unsupported summary once.")
        revised = row.model_copy(update={"participant_brief": text.replace(self.brief_omission + " ", "", 1)})
        if revised == row:
            raise ValueError("The participant instruction must support one exact sentence-level removal.")
        return design.model_copy(update={"inventory": [revised if item.source_id == self.source_id else item
                                                        for item in design.inventory]})

    def revise_source(self, previous: Source) -> Source:
        paragraph = f"\n\n{self.omitted_paragraph}\n\n"
        if (previous.id != self.source_id or previous.text.count(paragraph) != 1
                or previous.text.count(self.old_label) != 1 or self.old_label == self.new_label
                or any("\n" in item or "\r" in item for item in (self.old_label, self.new_label))):
            raise ValueError("A retained recipient repair needs one exact paragraph and one ordinary label.")
        corrected = previous.text.replace(paragraph, "\n\n", 1).replace(self.old_label, self.new_label, 1)
        return previous.model_copy(update={"text": corrected})
