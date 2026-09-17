## Base operating system and uv
## Pin both image digests; uv supplies Python, so no Python base image is needed.
FROM debian:bookworm-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171
COPY --from=ghcr.io/astral-sh/uv:0.11.26@sha256:3d868e555f8f1dbc324afa005066cd11e1053fc4743b9808ca8025283e65efa5 /uv /usr/local/bin/uv

## Operating-system tools
## Certificates support HTTPS downloads, Bash runs startup commands, and Git serves /version/.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates bash git \
    && rm -rf /var/lib/apt/lists/*

## Python behavior and installation paths
## Show logs immediately and avoid bytecode files; keep Python and packages outside source mounts.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=3.8.20 \
    PATH=/opt/venv/bin:$PATH

## Application working directory and writable data directories
## Relative paths in application settings and startup commands depend on this working directory.
WORKDIR /sr_project_stuff/code
RUN mkdir -p /sr_project_stuff/logs /sr_project_stuff/DBs /sr_project_stuff/cache_dir
## Dependency declarations and managed Python
## Copy only dependency inputs and README metadata, then download the selected Python patch.
COPY pyproject.toml uv.lock README.md ./
RUN uv python install "$UV_PYTHON"

## Interpreter selection after installation
## Subsequent uv commands use the installed managed Python and cannot download another interpreter.
ENV UV_PYTHON_DOWNLOADS=never UV_MANAGED_PYTHON=1

## Locked dependencies and SQLAlchemy C extensions
## Install runtime dependencies plus the local group; reject stale lockfiles.
## Temporarily add compiler tools for source builds, verify the extensions, then remove those tools.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && uv sync --locked --no-default-groups --group local --managed-python --no-python-downloads \
    && python -c "import sqlalchemy.cprocessors, sqlalchemy.cresultproxy, sqlalchemy.cutils" \
    && apt-get purge -y --auto-remove gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

## Runtime settings location
## Compose mounts the docker directory and creates its missing .env from the shared sample.
## This link exposes that file at the outer .env path expected by Django; no settings enter the image.
RUN ln -s docker/.env /sr_project_stuff/.env

## Default command
## Compose supplies the development checkout and overrides this shell with the web startup commands.
CMD ["/bin/bash"]
