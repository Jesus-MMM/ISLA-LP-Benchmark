# ============================================================
# ISLA LP Benchmark v1.8.0 — Docker Image
# Uses python:3.12-slim (lightweight, wide compatibility)
# ============================================================

FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgomp1 \
    coinor-cbc \
    && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock .

RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-interaction --no-ansi

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    coinor-cbc \
    && rm -rf /var/lib/apt/lists/* && \
    adduser --disabled-password --gecos '' --uid 1000 appuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser data/ ./data/

USER appuser
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["--help"]
