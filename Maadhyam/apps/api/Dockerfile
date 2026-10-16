FROM ghcr.io/astral-sh/uv:0.13.0 AS uv
FROM python:3.13-slim
COPY --from=uv /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 PATH="/app/.venv/bin:$PATH" PORT=8080
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable && useradd --uid 10001 --create-home appuser
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8080')+'/api/health',timeout=2)"
CMD ["sh", "-c", "exec uvicorn maadhyam_api.main:app --host 0.0.0.0 --port ${PORT:-8080} --no-access-log --log-level info"]
