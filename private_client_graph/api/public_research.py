"""Anonymous, read-only delivery of the exact curated research publication."""
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from private_client_graph.application.public_research import read_public_research

router = APIRouter()


def _publication_response(*, download: bool = False) -> Response:
    try:
        content = read_public_research()
    except (OSError, ValueError, KeyError, TypeError):
        return JSONResponse({'error': {'message': 'Published research results are unavailable.'}}, status_code=503)
    headers = {'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff'}
    if download:
        headers['Content-Disposition'] = 'attachment; filename="research-results.v1.json"'
    return Response(content, media_type='application/json', headers=headers)


@router.get('/api/research-results')
def research_results() -> Response:
    return _publication_response()


@router.get('/api/research-results/download')
def download_research_results() -> Response:
    return _publication_response(download=True)
