"""Reference reservation and transaction failures from proposal persistence."""

from private_client_graph.application.proposal_contracts import ReferenceOwner


class DuplicateReference(Exception):
    def __init__(self, owner: ReferenceOwner):
        super().__init__("The external Matter reference is already reserved")
        self.owner = owner


class ProposalPersistenceFailure(Exception):
    """A write either rolled back or reached a commit whose outcome is unknown."""

    def __init__(self, *, ambiguous: bool):
        super().__init__(
            "Proposal persistence outcome is unknown"
            if ambiguous
            else "Proposal write rolled back"
        )
        self.ambiguous = ambiguous
