FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=300 \
    UV_HTTP_RETRIES=10

WORKDIR /bot

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY config_data ./config_data
COPY handlers ./handlers
COPY keyboards ./keyboards
COPY middleware ./middleware
COPY states ./states
COPY utils ./utils
COPY loader.py main.py init_webhook.py ./

CMD ["/bot/.venv/bin/python", "main.py"]
