"""Thin HTTP boundary for the fixed synthetic professional-review workspace."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from private_client_graph.application.contracts import AnalysisError

from private_client_graph.application.errors import AnalysisFailure

from private_client_graph.application.case_analysis import analyse_case, get_case
from private_client_graph.application.contracts import (
    AnalysisRequest,
    CaseAnalysis,
    CaseDetail,
)

app = FastAPI(title="Private Client Graph")


@app.get("/api/case-01", response_model=CaseDetail)
def case_detail() -> CaseDetail:
    return get_case()


@app.post("/api/case-01/analysis", response_model=CaseAnalysis)
def case_analysis(request: AnalysisRequest) -> CaseAnalysis:
    return analyse_case(request.mode)


@app.exception_handler(AnalysisFailure)
async def analysis_failure(request: Request, exc: AnalysisFailure) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.error.model_dump()}
    )


@app.exception_handler(RequestValidationError)
async def invalid_request(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    error = AnalysisError(
        stage="request", message="Choose live or sample analysis only."
    )
    return JSONResponse(status_code=422, content={"error": error.model_dump()})
