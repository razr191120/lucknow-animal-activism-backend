FROM python:3.10-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/
COPY start.sh ./

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["./start.sh"]
