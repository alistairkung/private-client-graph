"""Safe request-local failures for Matter Proposal operations."""

from datetime import datetime

from pydantic import BaseModel, Field

from .proposal_contracts import ReferenceOwner


class ProposalError(BaseModel):
    code: str
    source_number: int | None = Field(default=None, exclude_if=lambda value: value is None)
    message: str
    retryable: bool = False
    outcome_unknown: bool = False
    resets_at: datetime | None = None
    existing_resource: ReferenceOwner | None = None


class ProposalFailure(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 422,
        source_number: int | None = None,
        retryable: bool = False,
        outcome_unknown: bool = False,
        resets_at: datetime | None = None,
        existing_resource: ReferenceOwner | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error = ProposalError(
            code=code,
            source_number=source_number,
            message=message,
            retryable=retryable,
            outcome_unknown=outcome_unknown,
            resets_at=resets_at,
            existing_resource=existing_resource,
        )
