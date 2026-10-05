import asyncio
from pathlib import Path

import httpx
import pytest

from private_client_graph.api.app import create_app
from private_client_graph.api.auth import CSRF_COOKIE

PDF = Path(__file__).parent / 'fixtures' / 'synthetic-proposal.pdf'
FIELDS = {'external_reference': 'Example/48', 'matter_title': 'Example family',
          'source_title': 'Fictional attendance note', 'synthetic_confirmation': 'true'}


def security_headers(client):
    return {
        "origin": "https://testserver",
        "x-csrftoken": client.cookies[CSRF_COOKIE],
    }


def submit(client, *, fields=None, pdf=None):
    return client.post('/api/matter-proposals', data=fields or FIELDS,
        files={'pdf': ('example.pdf', PDF.read_bytes() if pdf is None else pdf, 'application/pdf')},
        headers=security_headers(client))


@pytest.mark.parametrize('confirmation', [None, 'false', 'True', 'yes', ''])
def test_attestation_precedes_pdf_parsing_and_database(
    confirmation, authenticated_client, monkeypatch, tracked_upload_files
):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    client = authenticated_client(create_app())
    fields = {**FIELDS}
    if confirmation is None:
        del fields['synthetic_confirmation']
    else:
        fields['synthetic_confirmation'] = confirmation
    response = submit(client, fields=fields, pdf=b'not a PDF')
    assert response.status_code == 422
    assert response.json()['error']['code'] == 'synthetic_confirmation_required'
    assert tracked_upload_files
    assert all(file.closed for file in tracked_upload_files)


@pytest.mark.parametrize(
    "field,value",
    [
        ("external_reference", "R" * 101),
        ("matter_title", "   "),
        ("source_title", "Line one\nline two"),
    ],
)
def test_metadata_validation_precedes_pdf_parsing_and_database(
    field, value, authenticated_client, monkeypatch, tracked_upload_files
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = authenticated_client(create_app())

    response = submit(client, fields={**FIELDS, field: value}, pdf=b"not a PDF")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_metadata"
    assert tracked_upload_files
    assert all(file.closed for file in tracked_upload_files)


@pytest.mark.parametrize(
    "change",
    ["missing_pdf", "extra_pdf", "extra_field", "repeated_field", "pdf_is_text", "title_is_file"],
)
def test_intake_requires_exactly_one_pdf_and_each_text_field_once(
    change, authenticated_client, monkeypatch
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = authenticated_client(create_app())
    parts = [(name, (None, value)) for name, value in FIELDS.items()]
    parts.append(("pdf", ("example.pdf", b"not a PDF", "application/pdf")))
    if change == "missing_pdf":
        parts.pop()
    elif change == "extra_pdf":
        parts.append(("pdf", ("second.pdf", b"not a PDF", "application/pdf")))
    elif change == "extra_field":
        parts.append(("unexpected", (None, "extra value")))
    elif change == "repeated_field":
        parts[2] = ("matter_title", (None, "Another title"))
    elif change == "pdf_is_text":
        parts[-1] = ("pdf", (None, "not a file"))
    elif change == "title_is_file":
        parts[1] = ("matter_title", ("title.txt", b"Fictional title", "text/plain"))
        parts[-1] = ("pdf", (None, "not a file"))

    response = client.post(
        "/api/matter-proposals", files=parts, headers=security_headers(client)
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_form"


@pytest.mark.parametrize(
    "content_type,body",
    [
        ("application/json", b"{}"),
        ("multipart/form-data", b"missing boundary"),
        ("multipart/form-data; boundary=synthetic", b"malformed multipart bytes"),
    ],
)
def test_malformed_or_non_multipart_intake_is_a_safe_validation_failure(
    content_type, body, authenticated_client, monkeypatch
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = authenticated_client(create_app())

    response = client.post(
        "/api/matter-proposals",
        content=body,
        headers={**security_headers(client), "content-type": content_type},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_form"


def test_a_pdf_over_ten_mebibytes_is_rejected_and_closed(
    authenticated_client, monkeypatch, tracked_upload_files
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = authenticated_client(create_app())
    pdf = PDF.read_bytes().ljust(10 * 1024 * 1024 + 1, b" ")

    response = submit(client, pdf=pdf)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "pdf_too_large"
    assert tracked_upload_files
    assert all(file.closed for file in tracked_upload_files)


def multipart_prefix():
    boundary = "synthetic-intake-boundary"
    parts = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
        for name, value in FIELDS.items()
    ]
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="pdf"; filename="example.pdf"\r\n'
        'Content-Type: application/pdf\r\n\r\n'
    )
    return boundary, "".join(parts).encode()


def test_streamed_oversized_request_stops_and_closes_the_temporary_pdf(
    authenticated_client, monkeypatch, tracked_upload_files
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    app = create_app()
    client = authenticated_client(app)
    boundary, prefix = multipart_prefix()
    sent_chunks = []

    async def body():
        yield prefix
        for index in range(20):
            sent_chunks.append(index)
            yield b"A" * (1024 * 1024)
        yield f"\r\n--{boundary}--\r\n".encode()

    async def post():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app),
            base_url="https://testserver",
            cookies=dict(client.cookies),
        ) as streaming_client:
            return await streaming_client.post(
                "/api/matter-proposals",
                content=body(),
                headers={
                    **security_headers(client),
                    "content-type": f"multipart/form-data; boundary={boundary}",
                },
            )

    response = asyncio.run(post())

    assert "content-length" not in response.request.headers
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "pdf_too_large"
    assert len(sent_chunks) < 20
    assert tracked_upload_files
    assert all(file.closed for file in tracked_upload_files)


def test_truncated_multipart_is_rejected_and_closes_the_partial_pdf(
    authenticated_client, monkeypatch, tracked_upload_files
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = authenticated_client(create_app())
    boundary, prefix = multipart_prefix()

    response = client.post(
        "/api/matter-proposals",
        content=prefix + PDF.read_bytes(),
        headers={
            **security_headers(client),
            "content-type": f"multipart/form-data; boundary={boundary}",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_form"
    assert tracked_upload_files
    assert all(file.closed for file in tracked_upload_files)


@pytest.mark.parametrize("pdf_is_valid", [False, True])
def test_temporary_pdf_is_closed_after_acquisition_or_a_later_failure(
    pdf_is_valid, authenticated_client, monkeypatch, tracked_upload_files
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = authenticated_client(create_app())

    response = submit(client, pdf=PDF.read_bytes() if pdf_is_valid else b"not a PDF")

    if pdf_is_valid:
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "reference_unavailable"
    else:
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_pdf"
    assert tracked_upload_files
    assert all(file.closed for file in tracked_upload_files)


def test_pdf_filename_and_declared_media_type_are_advisory(
    authenticated_client, monkeypatch, tracked_upload_files
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = authenticated_client(create_app())

    response = client.post(
        "/api/matter-proposals",
        data=FIELDS,
        files={"pdf": ("fictional-note.txt", PDF.read_bytes(), "text/plain")},
        headers=security_headers(client),
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "reference_unavailable"
    assert tracked_upload_files
    assert all(file.closed for file in tracked_upload_files)


@pytest.mark.parametrize("body", [
    {},
    {"matter_proposal_id": "not-a-uuid"},
    {
        "matter_proposal_id": "00000000-0000-0000-0000-000000000049",
        "current_graph": {"entities": [], "relationships": [], "evidence": []},
    },
    {
        "matter_proposal_id": "00000000-0000-0000-0000-000000000049",
        "authoritative_source": {"title": "Injected", "text": "Injected"},
    },
])
def test_confirmation_rejects_missing_invalid_or_arbitrary_matter_state_before_database(
    body, authenticated_client, monkeypatch,
):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = authenticated_client(create_app())

    response = client.post(
        "/api/matters",
        json=body,
        headers=security_headers(client),
    )

    assert response.status_code == 422
    assert response.json() == {"error": {
        "code": "invalid_confirmation",
        "message": "Supply exactly one valid Matter Proposal identifier.",
    }}
