"""Verify the private ordered Source release without loading its reference."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from private_client_graph.models.source import Source
from .artifacts import checksum
from .retained_inputs import value_digest


Digest = Annotated[str, StringConstraints(pattern=r'^[a-f0-9]{64}$')]
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
