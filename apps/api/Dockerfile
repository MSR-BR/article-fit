FROM python:3.13.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*
COPY pyproject.toml requirements.lock requirements-dev.lock README.md ./
COPY apps ./apps
COPY tests ./tests
RUN pip install --no-cache-dir --require-hashes -r requirements.lock && pip install --no-cache-dir --no-deps .

FROM base AS runtime
RUN rm -rf /usr/local/lib/python3.13/site-packages/pip /usr/local/lib/python3.13/site-packages/pip-* && \
    rm -f /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.13 && \
    useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "journal_matcher_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test
RUN pip install --no-cache-dir --require-hashes -r requirements-dev.lock
RUN ruff check apps tests && ruff format --check apps tests && mypy apps/api/src apps/worker/src && pytest
