"""Read one explicitly released, source-only workload from private custody."""

import base64
import os
import re
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import TypeAdapter
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from private_client_graph.research.exploratory_release import (
    Digest, ExploratoryManifest, ExploratoryRelease, ExploratoryWorkload,
)
from private_client_graph.research.exploratory_reference import ConsensusReference, read_reference


_DIGEST = TypeAdapter(Digest)


def mount_exploratory_workload(app: FastAPI, prefix: str) -> None:
    """Configure the private viewer only when all release settings are present."""
    directory = os.getenv('PCG_EXPLORATORY_WORKLOAD_DIR')
    digest = os.getenv('PCG_EXPLORATORY_MANIFEST_SHA256')
    token = os.getenv('PCG_EXPLORATORY_ACCESS_TOKEN')
    reference = os.getenv('PCG_EXPLORATORY_REFERENCE_FILE')
    reference_digest = os.getenv('PCG_EXPLORATORY_REFERENCE_SHA256')
    if all(value is None for value in (directory, digest, token, reference, reference_digest)):
        return
    if not directory or not digest or not token or not re.fullmatch(r'[A-Za-z0-9_-]{32,}', token):
        raise ValueError('Exploratory Workbench requires a directory, manifest digest and private access token.')
    if (reference is None) != (reference_digest is None):
        raise ValueError('The exploratory reference requires both its file and exact commitment.')
    release = ExploratoryRelease(Path(directory), _DIGEST.validate_python(digest))
    require_private_owner(app, token)

    @app.get(f'{prefix}/exploratory-workload', response_model=ExploratoryManifest)
    def metadata() -> ExploratoryManifest:
        return _read_released_workload(release).manifest

    @app.get(f'{prefix}/exploratory-workload/sources', response_model=ExploratoryWorkload)
    def sources() -> ExploratoryWorkload:
        return _read_released_workload(release)

    if reference is not None and reference_digest is not None:
        _mount_reference(app, prefix, release, Path(reference), _DIGEST.validate_python(reference_digest))


def require_private_owner(app: FastAPI, token: str) -> None:
    """Protect all routes that can read or run against private benchmark artifacts."""
    if not re.fullmatch(r'[A-Za-z0-9_-]{32,}', token):
        raise ValueError('Private Workbench requires an owner token.')
    expected_credentials = base64.b64encode(f'owner:{token}'.encode())

    @app.middleware('http')
    async def require_local_owner(request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.client is None or request.client.host not in {'127.0.0.1', '::1'}:
            return JSONResponse({'detail': 'Private Workbench is local only.'}, status_code=403)
        scheme, _, credentials = request.headers.get('authorization', '').partition(' ')
        if scheme.lower() != 'basic' or not secrets.compare_digest(credentials.encode(), expected_credentials):
            return JSONResponse(
                {'detail': 'Owner sign-in required.'}, status_code=401,
                headers={'WWW-Authenticate': 'Basic realm="PCG owner Workbench", charset="UTF-8"'},
            )
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response


def _mount_reference(app: FastAPI, prefix: str, release: ExploratoryRelease, path: Path, digest: str) -> None:
    @app.get(f'{prefix}/exploratory-workload/reference', response_model=ConsensusReference)
    def reference() -> ConsensusReference:
        workload = _read_released_workload(release)
        try:
            return read_reference(path, digest, workload_id=workload.manifest.workload_id,
                                  source_file_sha256=workload.manifest.source_file_sha256,
                                  sources=list(workload.sources))
        except (ValueError, OSError):
            raise HTTPException(409, 'The exploratory reference could not be verified.') from None


def _read_released_workload(release: ExploratoryRelease) -> ExploratoryWorkload:
    # Exceptions from local custody, such as a permission failure or invalid
    # input fields, can contain private paths or Source text.
    try:
        return release.read()
    except (ValueError, OSError):
        raise HTTPException(409, 'The released exploratory workload could not be verified.') from None
