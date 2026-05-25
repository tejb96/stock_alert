FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN UV_HTTP_TIMEOUT=1500 uv sync --locked --no-install-project

COPY . .
RUN UV_HTTP_TIMEOUT=1500 uv sync --locked

EXPOSE 8000

CMD ["sh", "-c", "uv sync --locked && exec uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload --log-level debug"]
