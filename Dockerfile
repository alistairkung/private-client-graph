FROM node:24-alpine AS frontend

WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build


FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS application

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
COPY private_client_graph/ ./private_client_graph/
COPY cases/ ./cases/
RUN uv sync --locked --no-dev

COPY --from=frontend /build/web/dist/ ./web/dist/

EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn private_client_graph.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
