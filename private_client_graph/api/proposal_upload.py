"""Bound multipart acquisition and close the request's temporary upload on all paths."""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Request
from starlette.datastructures import FormData, UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser

from private_client_graph.application.proposal_sources import MAX_PROPOSAL_SOURCES, MAX_TOTAL_PDF_BYTES
from private_client_graph.application.proposal_errors import ProposalFailure

# Metadata and multipart framing are bounded separately from the PDF payload.
MAX_REQUEST_BYTES = MAX_TOTAL_PDF_BYTES + 64 * 1024


@asynccontextmanager
async def proposal_form(request: Request) -> AsyncIterator[FormData]:
    content_type = request.headers.get("content-type", "").split(";")[0].strip()
    if content_type != "multipart/form-data":
        raise ProposalFailure(
            "invalid_form", "Submit one PDF and the required form fields."
        )
    parser = MultiPartParser(
        request.headers,
        _bounded_stream(request),
        max_files=MAX_PROPOSAL_SOURCES,
        max_fields=4,
        max_part_size=8192,
    )
    try:
        try:
            form = await parser.parse()
        except MultiPartException as exc:
            raise ProposalFailure(
                "invalid_form",
                "Submit at most five PDFs, at most 10 MiB combined, and the required form fields.",
            ) from exc
        if form.get("synthetic_confirmation") != "true":
            raise ProposalFailure(
                "synthetic_confirmation_required",
                "Confirm that the material is synthetic or fictional.",
            )
        _validate_form_parts(form)
        yield form
    finally:
        _close_parser_uploads(parser)


def _validate_form_parts(form: FormData) -> None:
    bundle = "sources" in form
    file_field = "pdfs" if bundle else "pdf"
    text_fields = {"external_reference", "matter_title", "synthetic_confirmation",
                   "sources" if bundle else "source_title"}
    uploads = form.getlist(file_field)
    maximum = MAX_PROPOSAL_SOURCES if bundle else 1
    if (set(form) != text_fields | {file_field} or not 1 <= len(uploads) <= maximum
            or len(form.multi_items()) != len(text_fields) + len(uploads)
            or any(not isinstance(form[name], str) for name in text_fields)
            or any(not isinstance(upload, UploadFile) for upload in uploads)):
        raise ProposalFailure("invalid_form", "Supply each required text field once and one PDF per Source.")


def _close_parser_uploads(parser: MultiPartParser) -> None:
    """Isolate the pinned Starlette 1.7.0 incomplete-upload cleanup dependency.

    Request.form() and FormData.close() reach only completed parts. The parser can
    return a form after a truncated final part without raising or including that
    part in the form, and it exposes no public close operation for all spools.
    Its private registry is therefore needed on both success and failure paths;
    the HTTP truncation and tempfile regression tests protect this dependency.
    """
    for temporary_file in parser._files_to_close_on_error:
        temporary_file.close()


async def _bounded_stream(request: Request) -> AsyncGenerator[bytes, None]:
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_REQUEST_BYTES:
            # The multipart parser closes temporary files when its stream raises.
            raise ProposalFailure(
                "pdf_too_large", "The combined PDF upload limit is 10 MiB.", status_code=413
            )
        yield chunk
