from .contracts import AnalysisError


class AnalysisFailure(Exception):
    """A safe, stage-aware failure with optional persisted-run traceability."""

    def __init__(self, error: AnalysisError, status_code: int = 500):
        super().__init__(error.message)
        self.error = error
        self.status_code = status_code
