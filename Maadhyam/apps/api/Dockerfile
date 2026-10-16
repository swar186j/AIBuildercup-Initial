FROM ghcr.io/astral-sh/uv:0.13.0 AS uv
FROM python:3.13-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable && useradd --uid 10001 --create-home app
USER 10001
ENV PATH="/app/.venv/bin:$PATH" PORT=8080
CMD ["sh", "-c", "exec uvicorn maadhyam_api.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
