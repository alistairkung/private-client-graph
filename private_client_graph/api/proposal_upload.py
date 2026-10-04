"""Bound multipart acquisition and close the request's temporary upload on all paths."""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Request
from starlette.datastructures import FormData, UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser

from private_client_graph.application.proposal_errors import ProposalFailure

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
# Metadata and multipart framing are bounded separately from the PDF payload.
MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES + 64 * 1024


@asynccontextmanager
async def proposal_form(request: Request) -> AsyncIterator[FormData]:
    if request.headers.get('content-type', '').split(';')[0].strip() != 'multipart/form-data':
        raise ProposalFailure('invalid_form', 'Submit one PDF and the required form fields.')
    parser = MultiPartParser(request.headers, _bounded_stream(request),
                             max_files=1, max_fields=4, max_part_size=2048)
    try:
        try:
            form = await parser.parse()
        except MultiPartException as exc:
            raise ProposalFailure('invalid_form', 'Submit exactly one PDF of at most 10 MiB and the required form fields.') from exc
        if form.get('synthetic_confirmation') != 'true':
            raise ProposalFailure('synthetic_confirmation_required',
                                  'Confirm that the material is synthetic or fictional.')
        required = {'external_reference', 'matter_title', 'source_title', 'synthetic_confirmation', 'pdf'}
        if set(form) != required or len(form.multi_items()) != len(required):
            raise ProposalFailure('invalid_form', 'Submit exactly one PDF and all required fields once.')
        if not isinstance(form['pdf'], UploadFile) or any(
            not isinstance(form[name], str) for name in required - {'pdf'}
        ):
            raise ProposalFailure('invalid_form', 'Submit exactly one PDF and the required text fields.')
        yield form
    finally:
        # Starlette can return an incomplete form for a truncated final part.
        # FormData.close() misses that part; the parser owns every spool, including
        # unfinished uploads. Close them all even when parsing never returns a form.
        for temporary_file in parser._files_to_close_on_error:
            temporary_file.close()


async def _bounded_stream(request: Request) -> AsyncGenerator[bytes, None]:
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_REQUEST_BYTES:
            # The multipart parser closes temporary files when its stream raises.
            raise ProposalFailure('pdf_too_large', 'The PDF upload limit is 10 MiB.', status_code=413)
        yield chunk
