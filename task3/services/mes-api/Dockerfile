FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim as tm_builder

WORKDIR /opt/mes-api/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen


FROM python:3.12-slim

WORKDIR /opt/mes-api/
COPY --from=tm_builder /opt/mes-api/.venv/ .venv/
COPY mes_api/ ./mes_api

ENV PATH="/opt/mes-api/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

EXPOSE 8001
CMD python3 -m mes_api
