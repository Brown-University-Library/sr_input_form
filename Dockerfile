FROM debian:bookworm-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171
COPY --from=ghcr.io/astral-sh/uv:0.11.26@sha256:3d868e555f8f1dbc324afa005066cd11e1053fc4743b9808ca8025283e65efa5 /uv /usr/local/bin/uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates bash git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=3.8.20 \
    PATH=/opt/venv/bin:$PATH

WORKDIR /sr_project_stuff/code
RUN mkdir -p /sr_project_stuff/logs /sr_project_stuff/DBs /sr_project_stuff/cache_dir
COPY pyproject.toml uv.lock README.md ./
RUN uv python install "$UV_PYTHON"

ENV UV_PYTHON_DOWNLOADS=never UV_MANAGED_PYTHON=1
# Preserve SQLAlchemy's optional C extensions, including ARM64 source builds.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && uv sync --locked --no-default-groups --group local --managed-python --no-python-downloads \
    && python -c "import sqlalchemy.cprocessors, sqlalchemy.cresultproxy, sqlalchemy.cutils" \
    && apt-get purge -y --auto-remove gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# The settings directory is mounted at runtime; its file is created on first startup.
RUN ln -s docker/.env /sr_project_stuff/.env

# Compose supplies the development checkout and the web startup command.
CMD ["/bin/bash"]
