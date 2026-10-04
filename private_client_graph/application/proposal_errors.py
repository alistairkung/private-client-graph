"""Safe request-local failures for Matter Proposal operations."""

from datetime import datetime

from pydantic import BaseModel

from .proposal_contracts import ReferenceOwner


class ProposalError(BaseModel):
    code: str
    message: str
    retryable: bool = False
    outcome_unknown: bool = False
    resets_at: datetime | None = None
    existing_resource: ReferenceOwner | None = None


class ProposalFailure(Exception):
    def __init__(self, code: str, message: str, *, status_code: int = 422,
                 retryable: bool = False, outcome_unknown: bool = False,
                 resets_at: datetime | None = None,
                 existing_resource: ReferenceOwner | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.error = ProposalError(code=code, message=message, retryable=retryable,
            outcome_unknown=outcome_unknown, resets_at=resets_at, existing_resource=existing_resource)
