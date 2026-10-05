"""Promote one reviewed Matter Proposal into accepted Matter state."""

from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from private_client_graph.persistence.matter_proposals import confirm_proposal
from private_client_graph.persistence.proposal_errors import ProposalPersistenceFailure

from .matters import MatterDetail
from .proposal_errors import ProposalFailure


def confirm_matter(proposal_id: UUID) -> MatterDetail:
    try:
        matter = confirm_proposal(proposal_id)
    except ProposalPersistenceFailure as exc:
        if exc.ambiguous:
            raise ProposalFailure(
                "confirmation_outcome_unknown",
                "The confirmation outcome is unknown. Check the Matter Ledger to see whether "
                "the Matter was created before taking further action.",
                status_code=503,
                outcome_unknown=True,
            ) from exc
        raise ProposalFailure(
            "confirmation_failed",
            "The Matter could not be created. The Matter Proposal remains available. "
            "You may retry confirmation.",
            status_code=503,
            retryable=True,
        ) from exc
    except (SQLAlchemyError, ValueError) as exc:
        raise ProposalFailure(
            "invalid_proposal",
            "The Matter Proposal could not be confirmed because its stored state is invalid. "
            "It remains available for review or discard.",
            status_code=409,
        ) from exc
    if matter is None:
        raise ProposalFailure(
            "confirmation_outcome_unknown",
            "This Matter Proposal is no longer available. If confirmation may have completed, "
            "check the Matter Ledger to find the accepted Matter.",
            status_code=404,
            outcome_unknown=True,
        )
    return matter
