"""Read one explicitly released, source-only workload from private custody."""

import base64
import json
import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from private_client_graph.models.source import Source
from private_client_graph.research.artifacts import checksum
from private_client_graph.research.retained_inputs import value_digest


Digest = Annotated[str, StringConstraints(pattern=r'^[a-f0-9]{64}$')]
_DIGEST = TypeAdapter(Digest)
_BUNDLE_FILES = {'manifest.json', 'sources.json'}


class ExploratoryManifest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    schema_version: Literal[1]
    workload_id: Annotated[str, StringConstraints(pattern=r'^exploratory-scale-65-[a-f0-9]{12}$')]
    workload_kind: Literal['exploratory_scale']
    qualification: Literal['unqualified']
    read_only: Literal[True]
    scored: Literal[False]
    source_count: Literal[65]
    source_file_sha256: Digest
    source_array_sha256: Digest


class ExploratorySource(Source):
    model_config = ConfigDict(extra='forbid', strict=True)


class ExploratoryWorkload(BaseModel):
    manifest: ExploratoryManifest
    sources: Annotated[list[ExploratorySource], Field(min_length=65, max_length=65)]


@dataclass(frozen=True)
class ExploratoryRelease:
    directory: Path
    manifest_sha256: str

    def read(self) -> ExploratoryWorkload:
        if (not self.directory.is_absolute() or self.directory.resolve() != self.directory
                or self.directory.stat().st_mode & 0o077
                or {entry.name for entry in self.directory.iterdir()} != _BUNDLE_FILES):
            raise ValueError('Exploratory workload requires a private, source-only directory.')
        manifest_bytes = self._read_file('manifest.json')
        if checksum(manifest_bytes) != self.manifest_sha256:
            raise ValueError('Exploratory manifest differs from the approved commitment.')
        manifest = ExploratoryManifest.model_validate_json(manifest_bytes)
        raw = self._read_file('sources.json')
        if checksum(raw) != manifest.source_file_sha256:
            raise ValueError('Exploratory Source file differs from the approved commitment.')
        sources = json.loads(raw)
        digest = value_digest(sources)
        if (digest != manifest.source_array_sha256
                or manifest.workload_id != f'exploratory-scale-65-{digest[:12]}'):
            raise ValueError('Exploratory Source order or workload identity differs from the approved commitment.')
        workload = ExploratoryWorkload(manifest=manifest, sources=sources)
        if (len({source.id for source in workload.sources}) != manifest.source_count
                or any(not all(value.strip() for value in (source.id, source.title, source.text))
                       for source in workload.sources)):
            raise ValueError('Exploratory Sources must have unique IDs and nonempty fields.')
        return workload

    def _read_file(self, name: str) -> bytes:
        path = self.directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
            raise ValueError('Exploratory workload files must be private regular files.')
        return path.read_bytes()


def mount_exploratory_workload(app: FastAPI, prefix: str) -> None:
    """Configure the private viewer only when all release settings are present."""
    directory = os.getenv('PCG_EXPLORATORY_WORKLOAD_DIR')
    digest = os.getenv('PCG_EXPLORATORY_MANIFEST_SHA256')
    token = os.getenv('PCG_EXPLORATORY_ACCESS_TOKEN')
    if directory is None and digest is None and token is None:
        return
    if not directory or not digest or not token or not re.fullmatch(r'[A-Za-z0-9_-]{32,}', token):
        raise ValueError('Exploratory Workbench requires a directory, manifest digest and private access token.')
    release = ExploratoryRelease(Path(directory), _DIGEST.validate_python(digest))
    expected_credentials = base64.b64encode(f'owner:{token}'.encode())

    @app.middleware('http')
    async def require_local_owner(request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.client is None or request.client.host not in {'127.0.0.1', '::1'}:
            return JSONResponse({'detail': 'Exploratory Workbench is local only.'}, status_code=403)
        scheme, _, credentials = request.headers.get('authorization', '').partition(' ')
        if scheme.lower() != 'basic' or not secrets.compare_digest(credentials.encode(), expected_credentials):
            return JSONResponse(
                {'detail': 'Owner sign-in required.'}, status_code=401,
                headers={'WWW-Authenticate': 'Basic realm="PCG owner Workbench", charset="UTF-8"'},
            )
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get(f'{prefix}/exploratory-workload', response_model=ExploratoryManifest)
    def metadata() -> ExploratoryManifest:
        return _read_released_workload(release).manifest

    @app.get(f'{prefix}/exploratory-workload/sources', response_model=ExploratoryWorkload)
    def sources() -> ExploratoryWorkload:
        return _read_released_workload(release)


def _read_released_workload(release: ExploratoryRelease) -> ExploratoryWorkload:
    # Exceptions from local custody, such as a permission failure or invalid
    # input fields, can contain private paths or Source text.
    try:
        return release.read()
    except (ValueError, OSError):
        raise HTTPException(409, 'The released exploratory workload could not be verified.') from None
