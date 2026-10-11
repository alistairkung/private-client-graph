"""Portable, verifiable snapshots; rendering and exporting never invoke models."""
import json
import zipfile
from pathlib import Path

from .artifacts import Bundle, checksum


def export_bundle(bundle: Bundle, destination: Path) -> Path:
    if destination.resolve().is_relative_to(bundle.path.resolve()):
        raise ValueError('Export must be outside the bundle')
    with bundle.execution_lock():
        files = sorted(p for p in bundle.path.rglob('*') if p.is_file()
                       and not any(part.startswith('.') for part in p.relative_to(bundle.path).parts))
        if any(p.is_symlink() for p in files):
            raise ValueError('Bundle exports cannot contain symlinks')
        contents = {p.relative_to(bundle.path).as_posix(): p.read_bytes() for p in files}
        contents.pop('CHECKSUMS.json', None)
        hashes = {name: checksum(data) for name, data in contents.items()}
        with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in contents.items():
                archive.writestr(name, data)
            archive.writestr('CHECKSUMS.json', json.dumps(hashes, indent=2) + '\n')
    return destination


def verify_export(path: Path) -> bool:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive members')
        if any(Path(n).is_absolute() or '..' in Path(n).parts for n in names):
            raise ValueError('Unsafe archive member')
        hashes = json.loads(archive.read('CHECKSUMS.json'))
        if set(names) != set(hashes) | {'CHECKSUMS.json'}:
            raise ValueError('Archive contents do not match checksum manifest')
        if any(checksum(archive.read(n)) != digest for n, digest in hashes.items()):
            raise ValueError('Archive checksum mismatch')
    return True
