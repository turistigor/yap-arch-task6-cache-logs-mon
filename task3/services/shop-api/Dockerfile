FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim as tm_builder

WORKDIR /opt/shop-api/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen


FROM python:3.12-slim

WORKDIR /opt/shop-api/
COPY --from=tm_builder /opt/shop-api/.venv/ .venv/
COPY shop_api/ ./shop_api

ENV PATH="/opt/shop-api/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

EXPOSE 8000
CMD python3 -m shop_api
