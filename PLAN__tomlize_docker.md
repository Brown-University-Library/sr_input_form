# Plan to tomlize Docker development

Prepared September 6, 2026, from branch `uv-docker-dev` at `a5aaa48d`. This is an implementation plan; preparing it does not change dependencies, environment files, application code, or containers.

Use the existing `pyproject.toml` and `uv.lock` for Docker as well as host and server work. Replace the Docker dependency installation with `uv sync`, load application settings from a mounted `.env` through the already-pinned `python-dotenv==1.0.1`, and remove the retired requirements and shell-settings workflow after validation. First make the declared Python 3.8 environment work; keep the intended future Python and package upgrades separate.

## Contents

- [Current state and scope](#current-state-and-scope)
- [Exact versions and the Python 3.8 question](#exact-versions-and-the-python-38-question)
- [Implementation sequence](#implementation-sequence)
- [Tricky issues and tentative resolutions](#tricky-issues-and-tentative-resolutions)
- [Verification and completion criteria](#verification-and-completion-criteria)
- [Original prompt](#original-prompt)

## Current state and scope

The [starting architecture report](REPORT__starting_docker_architecture.md) describes the earlier `45bd376b` checkout. Its successful Docker run used Python 3.9.25, Django 3.2.25, SQLAlchemy 1.3.12, and PyMySQL 1.1.2. Those are baseline observations, not the versions to adopt for the conversion.

The current checkout already incorporates these changes:

- Commit `d1355422` removed `Dockerfile.dev` **and changed Compose to select `Dockerfile`**. There is no need to restore the removed file or repeat that Compose change.
- Commit `a5aaa48d` added the architecture report. Thus the inspected history also contains this documentation commit after the removal mentioned in the prompt.
- `DockerTest.test_requirements_exists` in `disa_app/tests/test_other.py` still opens both Dockerfile names. That stale test needs replacement during implementation.

The remaining [Dockerfile](Dockerfile) still selects `python:3.9` and runs `pip install -r requirements_local.txt`. [Compose](docker-compose.yml) reads `config/settings_localdev_env.sh` as an `env_file` and sets `DISA_DJ__ENV_SETTINGS_PATH`; that flag causes [Django settings](config/settings.py) to bypass dotenv loading. Host/server work already loads the outer `../.env` using `load_dotenv(..., override=True)` and validates 26 required setting names.

The three-service arrangement remains Django, MySQL, and Adminer. Preserve the SQLite seed, MySQL seed/import behavior, data paths, development autoreload, and browse generation. The dependency conversion does not require a new deployment caller or a change to the companion database repository. Existing repository directives describing “Phase 1” retention of pip are historical constraints to update as this requested next phase is implemented.

## Exact versions and the Python 3.8 question

### Python precision must be made explicit

`pyproject.toml` currently declares `requires-python = ">=3.8,<3.9"`; `uv.lock` records the equivalent `==3.8.*`. Neither names an exact patch release. Python 3.9 is outside this declaration, even if the old Docker image works.

The existing local `.venv/bin/python -VV`, inspected without loading application settings, reports **Python 3.8.20**. Use 3.8.20 as the tentative Docker target. Before final implementation, compare the actual interpreter versions used by the existing uv server deployments. Local interpreter availability alone does not prove Linux/container compatibility or server parity.

To satisfy patch-level exactness in TOML itself, the preferred implementation is to narrow `requires-python` to `==3.8.20` once that selection is verified, then refresh `uv.lock` without upgrading package pins. This is a shared host/server constraint, so check those environments before adopting it. If their established 3.8 patch is different, resolve the choice explicitly. Retaining the current range would guarantee only Python 3.8 compatibility and must not be described as an exact patch pin.

Prefer a Debian base image with uv installing the agreed exact Python patch during the image build. A Python-specific base image is not required: uv can download and manage Python itself. Pin the Debian variant/image digest and uv release separately from the application's Python version. Keep an exact-version Python base image as a fallback if the managed interpreter has a demonstrated availability or compatibility problem on a required platform. [uv Python version documentation](https://docs.astral.sh/uv/concepts/python-versions/), [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/).

A build assertion should compare the installed `sys.version_info` with the TOML declaration so later edits cannot leave the Docker build on a different patch. Any exact version repeated in the build command or an optional `.python-version` file must follow that declaration and be checked for agreement. Installing Python through uv changes how the interpreter is supplied; it does not resolve the current TOML patch-version ambiguity by itself.

### Preserve the declared dependency pins

The runtime pins to preserve are:

| Package | Version |
| --- | --- |
| asgiref | 3.8.1 |
| certifi | 2024.7.4 |
| charset-normalizer | 2.0.12 |
| django | 3.2.25 |
| idna | 3.7 |
| pymysql | 1.1.1 |
| python-dotenv | 1.0.1 |
| pytz | 2024.1 |
| requests | 2.27.1 |
| sqlalchemy | 1.3.12 |
| sqlparse | 0.5.1 |
| typing-extensions | 4.12.2 |
| urllib3 | 1.26.19 |

Keep the existing `local`, `staging`, and `prod` groups. `local` and `staging` are empty; `prod` adds **mysqlclient==2.1.1**. Docker development should install the runtime dependencies plus `local`, consistent with its `mysql+pymysql` database URL. Production should install runtime dependencies plus `prod`. A group-specific dependency is still authoritative when that group is used; installing all groups in development would add an unnecessary native MySQL driver and would not reproduce the established local workflow.

Do not carry PyMySQL 1.1.2 from the old Docker requirements into TOML. Do not reintroduce `shellvars-py`, `pip-tools`, or their incidental packaging dependencies. `uv.lock` supplies exact resolved artifacts and dependencies; inspect any lockfile diff and reject unrelated version changes. Use `uv sync --locked` for builds and deployments so a stale lockfile fails rather than being silently rewritten. `--frozen` skips the freshness check and is unsuitable for this requirement. [uv locking and syncing documentation](https://docs.astral.sh/uv/concepts/projects/sync/).

## Implementation sequence

### 1. Establish an isolated comparison environment

Use a disposable copy of the current branch and the same companion repository commits and seed files recorded in the report. Preserve the existing branch and its completed removal commit. No mainline update, branch replacement, or dependency upgrade is needed to prepare this plan.

For later execution, choose a unique Compose name, remove or override the fixed container names, assign unused loopback ports, and point **every** bind mount and build context into the disposable directory. A Compose name alone does not isolate the current fixed names or host data paths. Use copied starter data, not the existing host databases or private host `.env` files. The report's temporary experiment may no longer exist or may contain edited data; recreate a clean baseline if needed.

Before broad edits, attempt a minimal Debian image with uv installing the selected Python 3.8 patch and the exact locked local dependencies. Capture interpreter/version output and the complete download, build, or import failure. Exercise imports of Django, SQLAlchemy, PyMySQL, and dotenv before database startup. Test the team's relevant architectures, including Linux ARM64 and Linux AMD64 where used.

### 2. Convert the single web Dockerfile to uv

1. Select a verified Debian variant pinned by digest and copy the uv binary from an explicitly versioned official uv image, preferably also pinned by digest. An equivalently pinned Debian-based uv image is another suitable starting point. Verify that the selected uv release can obtain the agreed Python 3.8 patch for each required architecture and read the existing lock format. Do not install uv through pip or use a moving `latest` tag.
2. Keep `WORKDIR /sr_project_stuff/code`, unbuffered output, and disabled bytecode writes. Ensure the log, SQLite, and cache directories exist. Provide CA certificates for build-time downloads, Bash for the current startup logic, the Git executable needed by `/version/`, and any demonstrated OS library/build prerequisites.
3. Set `UV_PYTHON_INSTALL_DIR=/opt/python` for the managed interpreter and `UV_PROJECT_ENVIRONMENT=/opt/venv` for application dependencies; put `/opt/venv/bin` first on `PATH`. Both directories must remain outside source/data mounts and persist in the final image. The virtual environment can refer to its underlying interpreter, so copying `/opt/venv` alone into a later image stage is insufficient. Start with a single-stage image to keep this straightforward.
4. Copy `pyproject.toml`, `uv.lock`, and any metadata files needed by the selected build command before dependency installation. This application currently has no build-system declaration and its lock entry is virtual; do not invent a package build just to install its dependencies.
5. Install the agreed interpreter explicitly during the build, for example `uv python install 3.8.20` if the tentative patch is adopted. Then install dependencies with `uv sync --locked --no-default-groups --group local --python 3.8.20 --managed-python --no-python-downloads`. The example patch must agree with TOML. Allow the initial Python download, then set `UV_PYTHON_DOWNLOADS=never` and `UV_MANAGED_PYTHON=1` for subsequent sync/run commands and container startup. This keeps interpreter acquisition at build time and prevents an incidental system Python from being selected. These controls and the managed installation directory are documented in the [uv environment reference](https://docs.astral.sh/uv/reference/environment/).
6. Verify the installed interpreter and distribution versions against TOML and the selected lock entries. Use Python 3.8's `importlib.metadata` to inspect distributions without installing or invoking pip. For any TOML parser used in a helper, account for Python 3.8 lacking `tomllib`; do not add an unpinned application dependency merely for this check.

Add `.dockerignore` rules for `.venv`, `.git`, caches, private `.env` files, local databases/logs, and generated browse/denormalized JSON. Keep tracked map/timeline data available wherever source is copied. Runtime `/version/` can still see Git metadata through the development source mount. Copy only the intended build inputs; never copy an actual environment file into an image layer. The uv Docker guide documents copying the uv binary, excluding host environments, and controlling environment placement. [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/).

### 3. Make python-dotenv the application settings loader everywhere

Keep the existing location contract: the application loads the file one directory above its code, which is `/sr_project_stuff/.env` inside Docker. Keep `python-dotenv==1.0.1`, the required-file error, the required-key checks, and `override=True`. That explicitly preserves existing host/server precedence: values in the selected file replace conflicting inherited application variables. Version 1.0.1 supports this behavior. [Pinned python-dotenv implementation](https://raw.githubusercontent.com/theskumar/python-dotenv/v1.0.1/src/dotenv/main.py).

For developers using both host and Docker workflows, the preferred host layout is:

```text
outer-directory/
├── .env                     # existing host/server settings
├── docker/
│   └── .env                 # Docker development settings
├── disa_dj_project/
├── stolen_relations_start_data/
├── DBs/
├── logs/
└── cache_dir/
```

Mount `../docker/.env` read-only at `/sr_project_stuff/.env`. The file still has the requested `.env` name, and Python loads it directly. Add a sanitized `sample_dot_env_docker.txt` beside the existing host sample. A fresh Docker-only setup could instead use `../.env`, but the separate source path prevents overwriting the already-established host configuration. Do not reuse or rewrite the existing outer `.env`, `.env_dev`, or `.env_prod` during migration.

Use explicit mounts for the application source, DBs, logs, cache directory, starter data, and selected `.env`, replacing the broad `../:/sr_project_stuff` mount. Starter data can be read-only; working databases, logs, cache, and generated files need their existing write access. Use a long-form file bind with `read_only: true` and `bind.create_host_path: false` so a missing source file fails instead of creating a directory. Document directory/file creation before startup. [Compose volume configuration](https://docs.docker.com/reference/compose-file/services/#volumes).

The Docker sample must preserve the current Docker settings, including:

- `DISA_DJ__DATABASES_JSON`: Django SQLite at `../DBs/dj_disa.sqlite`.
- `DISA_DJ__DATABASE_URL`: SQLAlchemy/PyMySQL at service `db`, port `3306`, database `stolenrelations`, with development credentials matching the MySQL service.
- Logs/cache and browse output paths relative to `/sr_project_stuff/code`.
- Internal browse URLs on `127.0.0.1:8000`, even if the published host port differs.
- All required authentication, staff/group, JSON, and application settings, using safe example identities and secrets.

Convert shell-style example declarations into plain dotenv assignments, keeping JSON valid and quoted. Compare parsed values from the tracked old Docker example with the new sample; do not substitute the existing host sample's SQLAlchemy SQLite URL. Test quoted JSON, empty values, and any interpolation-sensitive characters with the pinned loader.

Remove `web.env_file` and `DISA_DJ__ENV_SETTINGS_PATH` from Compose, and remove the bypass branch from `config/settings.py` so dotenv loading is unconditional. Remove the unused `FOO_KEY` and `DB_*` entries after confirming application code still does not read them. Preserve runtime infrastructure variables such as `PYTHONPATH` if needed.

Compose's own interpolation files, service `env_file`, and Python's dotenv loading are different mechanisms. Here Compose only mounts the application file; Python parses it. MySQL still receives its `MYSQL_*` startup variables from Compose because its entrypoint is not Python. Keep those development credentials aligned with the application URL. No application settings file needs to be parsed twice.

### 4. Run every Python process in the container environment

Move the long Compose command into a small tracked Bash startup script if that makes validation and error handling clearer. Preserve the current order: wait for MySQL, copy SQLite and browse seeds only if missing, launch browse generation, then start Django. Preserve the working directory; several paths depend on it. End with `exec` for the server process so stop signals reach it.

At startup, run a locked local sync against the mounted TOML/lockfile with `--offline` and the same exact managed Python version selected at build time. Keep Python downloads disabled; the interpreter in `/opt/python` and environment in `/opt/venv` must already be usable. This checks that the mounted checkout still matches its lockfile and installed environment without downloading replacements. If the requested interpreter is absent or changed dependencies cannot be satisfied from the built image, fail with an instruction to rebuild. Verify this behavior with the selected uv release.

After that successful sync, use `uv run --no-sync` for the browse launcher and Django. For interactive management commands, document `uv run --locked --offline --group local ...`. Host and server commands continue to use their existing uv environment/group conventions. Dependency edits require an updated lockfile and `docker compose up --build`; source edits retain autoreload. This startup design must be tested with both an unchanged checkout and an intentionally stale lockfile.

Change `generate_browse_data_in_background.py` to launch its child with `sys.executable` instead of bare `python3`. This makes the child use the parent's interpreter on Docker and hosts alike. Do not infer generator success from a running web server: inspect completion and output separately. Update the generator's old activated-environment usage comment to the equivalent uv command.

### 5. Retire the old files and update maintained instructions

Once the new path passes the checks below, delete all six files:

```text
config/requirements_base.in
config/requirements_base.txt
config/requirements_local.in
config/requirements_local.txt
config/requirements_server.in
config/requirements_server.txt
```

Delete `config/settings_localdev_env.sh` after its example values and useful explanations have moved to the Docker dotenv sample and README. Remove executable/configuration references to these files and to shellvars. The user's requested retirement includes cleanup; there is no need to keep a second dependency list for rollback.

Update `README.md` and `AGENTS.md` to describe the completed conversion, the two host-side `.env` locations, file precedence, interpreter/group selection, and the container environment. Correct the README's repository name, use `docker compose`, and replace the mistaken rebuild explanation with `docker compose up --build`. Document initial seed prerequisites, file creation, restart after environment edits, uv management/test commands, and the `/opt/venv/bin/python` interpreter path for IDE attachment.

Extend `.gitignore` to exclude actual `.env` files, variants, and applicable caches while retaining sanitized samples. Review any deployment/cron/IDE commands maintained outside this Git repository for legacy invocations; migrate active commands before declaring the old workflow retired. No tracked CI or deployment caller was found in the inspected application checkout. Existing uv callers should be checked for compatibility rather than replaced without a need.

Replace the obsolete Docker requirements test with meaningful checks for the new behavior. Prioritize version agreement, missing/stale configuration failures, dotenv precedence, and the child's interpreter. Use actual image/startup validation for Docker behavior instead of relying solely on searches for particular Dockerfile strings. Keep the starting report and this prompt as historical documentation; occurrences of `pip` in history are not active uses.

## Tricky issues and tentative resolutions

| Issue | Tentative approach and fallback |
| --- | --- |
| The remembered Python 3.8 failure has no recorded traceback | Reproduce in the minimal locked Linux environment first and retain the failure. Separate package installation, native compilation, imports, Django initialization, and MySQL access. Fix demonstrated build prerequisites or Python 3.8-incompatible application code while preserving pins. If a dependency is demonstrably incompatible, document the blocker and propose an explicit TOML change separately; do not silently return Docker to 3.9. |
| Exact Python patch is absent from TOML | Start from the observed local 3.8.20, compare deployed interpreters, and make one shared patch decision. Narrow TOML and refresh the lock only after this check. A range plus a pinned image is an alternative with weaker TOML precision, not completion of patch-level exactness. |
| Managed Python availability or compatibility differs by platform | First verify uv's exact Python download and application imports on the selected Debian variant for each required architecture. Pin uv and record the managed Python build used; a Python patch identifies the language release, while the supplied binary build also matters for reproduction. If this approach fails, investigate the specific OS/library or download issue, then consider a verified exact-version Python image as a fallback while keeping TOML's version constraint. |
| SQLAlchemy 1.3.12 or production mysqlclient needs a source build | Capture wheel/build selection for the actual platform. Add demonstrated OS compiler/header/library requirements; keep Python package pins unchanged. Build-isolation tooling is distinct from installed application dependencies and can vary: if a failure involves it, constrain the build tooling explicitly with uv configuration or use a verified compatible artifact, recording the decision. Do not install missing application packages with ad hoc pip commands. |
| Host `.venv` or broad mounts override image contents | Use `/opt/venv` and explicit mounts. Test with a host `.venv` present and verify both server and generator paths. A container environment volume is an alternative, but requires additional refresh rules when dependencies change. |
| The selected `.env` contains host database paths or inherited values conflict | Use the dedicated Docker sample and explicit mount. Preserve `override=True`, validate both database targets without printing credentials, and retain the test runner's later fixture override. A future switch to environment-first precedence would be a separate behavior change. |
| MySQL readiness is weaker than application readiness | The existing TCP loop can succeed before credentials/schema are usable. Initially preserve and observe its behavior. If first-run tests expose failures, use a bounded authenticated readiness check that confirms required tables, with clear timeout errors; a health dependency can supplement this but cannot prove application schema readiness alone. |
| MySQL data persistence is already ambiguous | The named `db_data` volume is unused and MySQL uses an anonymous volume. Keep restart checks, document the current limitation, and do not run teardown with volume deletion on working data. Moving to a named volume requires an explicit export/restore and verification step; avoid accidentally attaching an empty volume over existing data as part of this conversion. |
| Browse generation is asynchronous and writes output directly | Wait for completion before comparison and inspect child errors. Use a foreground generation run for deterministic verification after the startup job ends. Better supervision or atomic output replacement can be a follow-up unless required to correct a demonstrated conversion failure. |
| Existing interface errors resemble regressions | Compare against the report's two JavaScript errors and its incomplete workflow coverage. Check persisted fields and output, not HTTP 200 alone. Preserve the internal port 8000 for the browse proxy and use a recognized Host header or disposable login for alternate-port checks. |

**BIRKIN-FEEDBACK — incorporated:** “note that `uv` can install its own version of python, so you _might_ not need a python-specifc image.” The preferred build now starts from Debian and lets uv install Python. The installation sequence, interpreter paths, runtime download policy, and verification criteria above and below follow that choice.

## Verification and completion criteria

Implementation validation must use disposable data and distinguish successful checks from work still pending.

1. **Dependency and interpreter agreement:** validate lock freshness; build the web image; compare the actual Python patch and every runtime distribution against TOML/lock. Record the Debian and uv image digests and managed Python build. Verify that `/opt/venv/bin/python` resolves to the retained interpreter under `/opt/python`, and that the finished image can start Python with networking disabled and source mounts present. Verify absence of old shellvars/pip-tools dependencies in the application environment. Independently sync `local`, `staging`, and `prod` in appropriate disposable environments so one group's installed packages cannot hide another's missing dependency. Production's native build check may need its server OS prerequisites.
2. **Settings behavior:** check the required file, all 26 required keys, valid JSON, and both effective database destinations using sanitized output. Include missing-file, missing-key, invalid-JSON, conflicting-inherited-value, and Docker-versus-host-file cases. Verify test fixture routing survives dotenv loading and automated test authorization still comes from the process startup environment rather than the file.
3. **Application checks and tests:** in the isolated Docker stack run `docker compose exec web uv run --locked --offline --group local ./manage.py check`, then `docker compose exec web uv run --locked --offline --group local ./run_tests.py`. Use the guarded runner's manual `yes`, or its documented automated development authorization only for disposable development tests. Do not replace it with ordinary `manage.py test`. Recheck the host uv workflow after the shared settings change.
4. **Failure and rebuild behavior:** validate Compose and any Bash script, check that missing seeds/settings fail clearly, and deliberately test a stale lockfile in the disposable copy. Confirm normal startup does not alter TOML/lock. Change a dependency declaration and lock together in a disposable copy, verify the documented rebuild path, then restore the exact agreed pins. Verify source autoreload and restart after `.env` edits.
5. **Functional comparison:** repeat the report's login/logout, populated source dashboard, source/record/individual/group save and reload, deletion marker, browse search/details/CSV, Adminer login, map/timeline, and restart persistence checks. Verify `/version/` still works with Git available. Compare freshly generated browse counts using identical starting SQL, SQLite, and deletion state; do not run two generators simultaneously. Record known baseline errors separately from new failures.
6. **Coverage limits:** exercise relationship operations, relevant date/location widgets, privileged admin operations, permissions, and backup restoration if claiming broader equivalence than the report established. Restart persistence is not proof of teardown/recreation persistence. Retain all unverified areas explicitly in the implementation report.
7. **Retirement and review:** search maintained code, Docker files, scripts, tests, and instructions for active pip, pip-tools, requirements-file, shellvars, and shell-settings use. Verify that only intended files changed, no real `.env` entered Git or the image, all six requirements files and the old shell sample are gone, and the README works from a fresh disposable checkout. Preserve historical reports. Do not commit automatically.

Rollback should use the recorded prior application image/source and matching copied settings while preserving data. Retain the verified prior image identifier and protect both databases before rollout. Restoring an old dependency environment does not require keeping live requirements files in the converted checkout, and does not justify deleting/reinitializing MySQL volumes.

This planning pass reviewed repository configuration, dependency declarations, the architecture report, and relevant tool documentation; it also confirmed the local interpreter's patch version. It did **not** build a Python 3.8 Docker image, refresh the lockfile, run the application test suite, or verify deployed server versions. Those are implementation checks above, not results already achieved.

## Original prompt

Goal: Make a plan to tomlize this project by managing dependencies via `uv` and `pyproject.toml`, and using a `.env` file for envars.

Context:

- Note that there has been one commit already to this branch, the removal of the file `disa_dj_project/Dockerfile.dev`.

- Review `disa_dj_project/REPORT__starting_docker_architecture.md` for a good overview of the starting-state of this project (before the `Dockerfile.dev` removal).

- I have a memory that in my early days of coming up with the Dockerfile, I had an problem getting something to run under python-3.8 -- so, for the Dockerfile, went with python-3.9.

  - Though we *do* intend to update this, I would like the updated Docker architecture to use *exactly* the versions of python and all dependencies listed in the `pyproject.toml` file.

Tasks:

- Make a plan to tomlize this project by:

  - retiring all use of `pip` and various `requirements` files in favor of using `uv` and `pyproject.toml`.
  - using a `.env` file to load envars via the python-package specified in the `pyproject.toml` file.

- Save the plan to `disa_dj_project/PLAN__tomlize_docker.md`

- Add to the plan any tricky issues you foresee, and a tentative approach or two to resolving them.

- Add this prompt to the bottom.
