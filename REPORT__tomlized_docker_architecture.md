# Tomlized Docker architecture

Repository naming update: paths, links, and any reproduced prompts below use the current name `sr_input_form`. Existing local checkout directory names may differ. Historical implementation findings otherwise retain their original scope.

Implemented September 6, 2026, on the existing `uv-docker-dev` branch, starting at `3b1cb7c8`. No commit was created. The [plan](PLAN__tomlize_docker.md) and [starting architecture report](REPORT__starting_docker_architecture.md) remain historical documents.

Docker now installs Python and dependencies through uv, uses the same TOML/lock declarations as host and server work, and loads application settings through python-dotenv. Python 3.8.20 and the existing dependency pins worked on Linux ARM64 and AMD64. Freshly generated browse records and the Portsmouth CSV export matched the earlier Docker implementation exactly.

## Contents

- [Decisions and resulting architecture](#decisions-and-resulting-architecture)
- [Build and dependency verification](#build-and-dependency-verification)
- [Settings, startup, and failure checks](#settings-startup-and-failure-checks)
- [Functional comparison](#functional-comparison)
- [Retirement and remaining limits](#retirement-and-remaining-limits)
- [Reproduction and evidence](#reproduction-and-evidence)
- [User clarifications](#user-clarifications)
- [Original implementation prompt](#original-implementation-prompt)

## Decisions and resulting architecture

The user's clarification supersedes the plan's tentative exact TOML patch pin: **`pyproject.toml` remains unchanged**, including `requires-python = ">=3.8,<3.9"`. `uv.lock` also remains unchanged. Docker selects exactly **3.8.20** with `UV_PYTHON` in the Dockerfile. Host/server deployments retain the declared Python 3.8 range; their exact deployed patch versions were not asserted or changed.

The existing branch was retained instead of updating mainline or creating another migration branch. Dependency declarations had already been converted to uv; this task specifically implements the remaining Docker phase. No new deployment caller or companion database change was necessary.

| Component | Result |
| --- | --- |
| Web base | Debian Bookworm slim, pinned by multi-architecture image digest |
| uv | Official binary image, release 0.11.26, pinned by multi-architecture digest |
| Python | uv-managed CPython 3.8.20 at `/opt/python` |
| Dependencies | Runtime pins plus `local`, at `/opt/venv`; `/opt/venv/bin` comes first on `PATH` |
| Application code | Live development bind at `/sr_project_stuff/code`; Git remains visible to `/version/` |
| Settings | Writable host `../docker/` mounted at `/sr_project_stuff/docker`; startup creates a missing `.env` from the sample, and `/sr_project_stuff/.env` links to it |
| Other web mounts | DBs, logs, cache directory, and read-only starter data; the broad outer-directory mount is removed |
| MySQL and Adminer | Existing companion build, credentials, import behavior, ports, and service arrangement retained |
| Startup | `docker-compose.yml` web command; locked offline sync, missing settings creation, prerequisite checks, MySQL wait, missing-file seed copies, browse launcher, Django |

The single-stage image retains both `/opt/python` and `/opt/venv`. Neither is covered by development mounts. Build inputs are explicit: TOML, lockfile, and README metadata. Actual environment files are never copied into image layers. `.dockerignore` also excludes host environments, Git, private dotenv files, databases, logs, caches, and generated browse/denormalized JSON; tracked map and timeline JSON remain available.

The Python download happens during the build. Later commands use `UV_PYTHON_DOWNLOADS=never` and `UV_MANAGED_PYTHON=1`. Startup performs `uv sync --locked --offline --no-default-groups --group local`, then runs the launcher and server through `uv run --no-sync`. Interactive Docker commands use `uv run --locked --offline --group local`. Build caches remain in the image so unchanged startup can validate/install the locked environment offline.

The browse launcher now uses `sys.executable`, keeping its child on the parent's interpreter on hosts and in Docker. The server command uses `exec` so stop signals reach uv and its server child. The former unlimited TCP wait now times out after 180 seconds with a useful database-log instruction; no schema/readiness redesign was needed in the successful clean-seed run.

These choices follow the official [uv Docker guidance](https://docs.astral.sh/uv/guides/integration/docker/), [lock/sync semantics](https://docs.astral.sh/uv/concepts/projects/sync/), and [environment-variable controls](https://docs.astral.sh/uv/reference/environment/).

## Build and dependency verification

Both the minimal compatibility experiment and the completed web Dockerfile built successfully for `linux/arm64` and `linux/amd64`. Both imported Django, SQLAlchemy, PyMySQL, and dotenv. No Python 3.8 incompatibility was reproduced, and no application package upgrade was needed. The first minimal ARM64 build successfully used SQLAlchemy 1.3.12 without its optional C extensions. Comparison with the old image showed that those extensions had previously been present, so the final build temporarily installs `gcc` and `libc6-dev`, builds the same locked package, asserts that all three extensions import, then removes the compiler packages. This preserves the earlier extension availability without adding compiler tools to the running environment.

| Pinned input | Identifier |
| --- | --- |
| Debian Bookworm slim | `sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171` |
| Official uv 0.11.26 | `sha256:3d868e555f8f1dbc324afa005066cd11e1053fc4743b9808ca8025283e65efa5` |
| Managed Python build | python-build-standalone `3.8.20+20241002`, GNU/Linux aarch64 and x86_64 stripped install archives |
| Validated ARM64 build before automatic setup | `sha256:e774d3b12f3e3a519aebd7c49aa39fb1f294aa8ea9110ef0fe9f104700b73540` |
| Validated AMD64 build before automatic setup | `sha256:acbdc16553c7cb9b67e055c739b3779f5241a948d72a449045a4738029ece059` |

The multi-architecture digests allow Docker to choose the CPU-specific image automatically. Apple Silicon uses ARM64; AMD64 covers typical Windows/Linux PCs. Intel Macs are outside the requested support scope. Both Linux instruction sets were exercised through Docker Desktop on this Apple Silicon host, with AMD64 emulation. Physical Windows and Linux host installations were not available for direct testing. Linux support did not require an alternative application design. Windows instructions use Docker's Linux-container mode and a WSL terminal; `.gitattributes` preserves Bash LF line endings.

All 13 local runtime distributions match the unchanged declarations: asgiref 3.8.1, certifi 2024.7.4, charset-normalizer 2.0.12, Django 3.2.25, idna 3.7, PyMySQL 1.1.1, python-dotenv 1.0.1, pytz 2024.1, requests 2.27.1, SQLAlchemy 1.3.12, sqlparse 0.5.1, typing-extensions 4.12.2, and urllib3 1.26.19. The old image's PyMySQL 1.1.2 was not carried forward. No shellvars, pip-tools, pip, setuptools, or wheel distribution is installed in the application environment.

Independent fresh environments installed `local` and `staging` successfully offline. A separate disposable Linux environment installed `prod` successfully, including mysqlclient 2.1.1; `MySQLdb` imported successfully. Its demonstrated OS build prerequisites were `gcc`, `libc6-dev`, and `default-libmysqlclient-dev`. The MySQL development library was installed only in that production validation container. The development image uses the compiler/libc headers temporarily for SQLAlchemy, then removes them. Build-isolation tools used while building source artifacts are distinct from the installed application distributions. Debian package repositories and isolated build-tool resolution are not immutable merely because the base image is pinned.

The original full guarded suite passed **67 tests on the host, 67 in ARM64 Docker, and 67 in AMD64 Docker**. Both Docker architectures also synchronized and ran Python with networking disabled and mounted source. `/opt/venv/bin/python` resolved into the retained architecture-specific `/opt/python/cpython-3.8.20-linux-…-gnu/bin/python3.8` installation, even with a host `.venv` present in the source mount.

Django checks passed with the existing `caches.W003` warning about a relative cache path. The requested relative path behavior was preserved. Ruff checks/formatting cover the new Python files, and Bash syntax and Compose configuration were checked.

## Settings, startup, and failure checks

The new Docker sample preserves all **28 parsed values** from the retired tracked Docker example, including the 26 required settings. This was compared using the pinned dotenv loader before deleting the old example. After validation, the repository-name correction updated `DISA_DJ__README_URL` in both sanitized samples to the current `sr_input_form` README; the other 27 Docker sample values remain as compared. JSON, authentication examples, MySQL service addressing, SQLite destination, log/cache paths, and internal browse URLs are unchanged.

`config/settings.py` unconditionally requires the outer `.env`, loads it with `override=True`, and retains required-key validation. Compose no longer supplies `web.env_file`, `DISA_DJ__ENV_SETTINGS_PATH`, `FOO_KEY`, or unused `DB_*` variables. MySQL keeps its separate Compose-supplied `MYSQL_*` entrypoint settings. The existing real host `.env`, `.env_dev`, `.env_prod`, and private shell snapshots were not rewritten or copied into the test stack.

| Check | Result |
| --- | --- |
| Valid Docker and host samples | Pass; Docker selects MySQL/PyMySQL plus Django SQLite, while the host sample retains SQLAlchemy SQLite |
| File precedence | Pass; a file value replaces a conflicting inherited application value |
| Missing file | Pass; settings fail even if the retired bypass variable is inherited |
| Missing required key | Pass; failure identifies the missing setting name |
| Invalid JSON | Pass; rejected during settings loading |
| Quoting/interpolation | Pass; quoted JSON, empty assignments, literal `$`/`#`, and `${NAME}` expansion were exercised |
| Test fixture routing | Pass; test settings override dotenv's database destinations after loading |
| Test authorization | Pass; real startup authorization permits disposable tests; placing authorization only in a disposable `.env` still refuses a noninteractive run |
| Missing file bind (initial implementation) | Originally failed deliberately; the later automatic-setup change below replaces this behavior |
| Missing seed | Pass; startup names the required starter file before waiting for MySQL |
| Missing interpreter | Pass; no runtime Python download occurs, and startup instructs the developer to rebuild |
| Stale TOML/lock pair | Pass; both image build and mounted startup reject it |
| Changed dependency and lock | Pass; a disposable idna 3.6 change cannot start from the old image offline, then succeeds offline after rebuilding; repository pins remain idna 3.7 |
| Unchanged startup | Pass; TOML and lock bytes remain unchanged |
| Environment and source reload | Pass; source changes trigger autoreload, settings changes appear after restart, and original sample values are restored |

## Functional comparison

Tests used fresh copies of the same four seed artifacts recorded in the starting report; SHA-256 checks matched all four. Initial MySQL counts matched: 2,001 citations, 2,950 references, 8,395 referents, and 239 groups. Both old and new generators used identical starting MySQL/SQLite/deletion state for the initial comparison.

The old web image was run separately against those disposable inputs to regenerate a fresh baseline. Both results contained **8,377 included referents, 18 excluded referents, 239 groups, and 205 references with groups**. All referent rows and group rows compared equal, not just their counts. Generation timestamps and elapsed times naturally differed. The initial measured generation runs were about 39 seconds for the earlier image and 53 seconds for the minimal new image without optional SQLAlchemy C extensions. The final build restores those extensions. These measurements are not a controlled performance benchmark.

| Workflow | Verified behavior |
| --- | --- |
| Login/logout | Correct and incorrect manual editor credentials; partner browse login/logout; editor logout |
| Dashboard and version | Populated source dashboard, `/version/`, root/info/login and static-data delivery |
| Source | Created disposable source 3196 via API, saved an author edit through the browser, checked persisted title/author |
| Record | Created record 3885 via API, saved page value `42` through the browser, checked its stored citation field and transcription |
| Individual | Created referent 10385 and saved/reloaded its name and age text through the API |
| Group | Created and updated a disposable group to count 3, estimated=true, with the labeled description; checked saved fields |
| Deletion | Created source 3197/referent 10386, deleted through the API, confirmed Django's marker and MySQL's retained source row |
| Browse | Populated narratives/table, Portsmouth search, no-match case, source/personal-details dialog |
| CSV export | 202 data rows, 15 columns, 377,128 bytes; parsed CSV exactly matches the baseline export |
| Map/timeline | Map tiles and clustered markers rendered; timeline displayed dated entries; tracked JSON served |
| Adminer | Logged into `db`/`stolenrelations`; all 43 tables listed |
| Access/error boundaries | Ordinary editor redirected from Django admin; nonexistent source and malformed JSON handled as expected |

The existing Vue error, `Cannot read properties of undefined (reading 'value')`, reappeared when opening the populated record editor, matching the starting report. It did not prevent the separately verified source/record/group/individual saves. The earlier new-record JavaScript `locations` error was not independently reproduced through a new-record browser submission in this pass; new-record creation was tested through the API. Raw GeoJSON/location IDs in browse narratives also remain as in the baseline.

An initial exploratory individual-details request incorrectly reused the read response's textual name type (`Unknown`) where the update API requires numeric ID 8. MySQL rejected that test payload. Repeating with the correct numeric value saved successfully; this was a validation-helper correction, not an application change. HTTP 200 alone was not treated as proof of a successful save.

Restarting both web and MySQL preserved the saved source, browser-edited author, record transcription/page field, individual, and group. Fresh generation then contained 8,378 included referents, 19 excluded referents, 240 groups, and 206 references with groups. The saved referent was included and the deletion-check referent was excluded. Original Docker sample values were restored and another completed startup confirmed that restoration. The checks also observed the autoreloader after a temporary source marker, then restored the exact source file.

The final image, with SQLAlchemy's C extensions restored and compiler packages removed, passed all 67 tests on each architecture. Its completed browse generation reproduced every referent and group row from the preceding saved-data run, and all 41 application checks passed again. That generation took about 45 seconds; the timing remains an observation rather than a controlled benchmark.

## Retirement and remaining limits

All six `config/requirements_{base,local,server}.{in,txt}` files and `config/settings_localdev_env.sh` are deleted. The obsolete Docker requirements-file test is replaced by behavior checks for dotenv loading and subprocess interpreter selection. Maintained Docker/README/agent instructions use uv, and old manual Python usage comments in related utilities now show uv commands.

The local `origin` remote now uses `git@github.com:Brown-University-Library/sr_input_form.git`. Documentation and the application's glossary link use that name; the existing checkout directory has not been renamed.

The README now documents fresh setup, both `.env` locations, file precedence, seed prerequisites, rebuilds, restart after settings changes, guarded tests, offline management commands, and the IDE interpreter path. The two outer deployment callers already source the uv callee and select `staging`/`prod`; their shared Python declarations remain compatible and the callers were not replaced. No maintained repository CI, cron, or IDE command requiring another migration was found. Live server crontabs and colleagues' private IDE configurations were not accessed.

This conversion retains the existing MySQL anonymous-volume behavior. Restart persistence is tested; teardown/recreation persistence, backup restoration, privileged Django-admin operations, the complete permissions matrix, relationship editing, and every date/location/vocabulary widget are not claimed. Adminer editing and actual IDE attachment were not tested. Real production authentication and deployment were not exercised. These limits prevent claiming comprehensive equivalence beyond the recorded workflows.

The companion MySQL and Adminer tags remain as before; only the web base and uv inputs are pinned in this change. Broader image lifecycle and database-storage changes remain separate work. The background browse generator is still asynchronous and writes output directly; server availability does not establish generation success.

### Automatic setup follow-up

At the user's request, `docker compose up --build` now includes working-directory and Docker-settings creation. Compose's directory binds create missing `DBs/`, `logs/`, `cache_dir/`, and `docker/` directories. The web startup command copies the tracked sample into `../docker/.env` only if that path is absent. Existing regular files, including empty or customized files, are preserved; a directory or symbolic link at that path fails with an explicit message. Copying preserves the sample's file ownership and permissions for host editing. No host/server settings file is mounted or rewritten.

The initial implementation's read-only file mount could not initialize a missing file before mounting it. It is replaced with a writable mount of the dedicated Docker-settings directory and an image-internal symbolic link from `/sr_project_stuff/.env` to `docker/.env`. This keeps Django's dotenv location unchanged and adds no service or dependency. The image contains only the link; actual settings are still created at runtime outside the repository. Existing three-repository installations can use `docker compose up --build` without the additional manual `mkdir` or sample-copy commands. The enclosing directory and repository clones are still required. This follow-up supersedes the original plan's deliberate missing-file failure and read-only settings mount. Directory creation follows [Compose's documented bind-mount behavior](https://docs.docker.com/reference/compose-file/services/#volumes).

Validation for this follow-up is retained separately under `/private/tmp/sr-compose-auto-setup-20260906/`. Both ARM64 and AMD64 images built successfully and created missing settings with networking disabled. Separate disposable cases passed for first-time directory/sample creation, preservation of customized and empty files, rejection of directories and symbolic links, and preservation of an unrelated host `.env`. One early check rapidly replaced a host file with a directory and observed Docker Desktop's previous file view; the repeated check and separate-directory cases confirmed the intended rejection. The ARM64 web service then started against the existing isolated test database, served the login page, passed Django checks with the same existing cache warning, and passed all 67 guarded tests. A settings-file replacement followed by a web restart retained the edit and loaded the new value through the image's symbolic link. Physical Windows/Linux host testing remains outside the available environment.

The updated image IDs are ARM64 `sha256:c441e702ebd68ffb53160a91773ed9f00c13d4b7dd42848802b9031e59e6fe78` and AMD64 `sha256:360bb66682c2ec97f4ab08104b0dd6681bbbd3ceaaa74418bcbdac48dc3f08ce`. Evidence includes `setup-results.json`, per-case `startup.log` files, architecture build logs, `tests.log`, `http-check.log`, and `restart-settings.log`. Python and dependency declarations remain unchanged.

### Startup command location follow-up

At the user's request, the startup commands now live in the existing `docker-compose.yml` under `services.web.command`. The separate startup script is removed, and Dockerfile's default command is Bash. Compose explicitly invokes Bash with the same startup body, preserving dependency checks, settings initialization, seed handling, the database wait, browse generation, and the final `exec`. The YAML uses a literal block and doubles dollar signs so Compose leaves variable expansion to Bash inside the container. The browse launcher docstring identifies the Compose command as its caller.

Validation of the inline command passed: Compose parsing, Bash syntax, byte-for-byte comparison of the running container command with the removed script, first-time settings creation, preservation of existing settings, Django checks, and all 67 guarded tests. The rebuilt ARM64 image is `sha256:4a8054c3b56e14f2843c1b852d9d8aa41b723fb09dfe9d0022271589f9e495cd`; evidence is under `/private/tmp/sr-compose-inline-20260906/`, including `results.json`, `build.log`, and `tests.log`. This relocation did not change the dependency declarations or startup behavior.

### Current build and test status

The build and startup use `uv sync --locked` directly to enforce TOML compatibility, lock freshness, and environment synchronization. Docker continues to select uv-managed Python 3.8.20, and the SQLAlchemy C-extension import assertion remains in the build. The current application suite contains 64 tests; earlier 67-test counts record the scope at those validation stages.

The current ARM64 image built successfully as `sha256:716671ba06c8cef2b1233930de86ad66ab88471c197e31abec8f54e971bdf92d`. It started with freshly initialized Docker settings and passed Django checks with the existing cache warning, plus all 64 guarded tests. All 64 host tests also passed. The SQLAlchemy C extensions still import without networking. Evidence is in `/private/tmp/sr-without-verifier-20260906/` and `/private/tmp/sr-verifier-removal-host-tests.log`. Python and dependency declarations remain unchanged.

## Reproduction and evidence

The disposable comparison root is `/private/tmp/disa-tomlize-docker-20260906/`. The disposable editor username is `docker_tomlized_audit`; its synthetic account is confined to the copied databases. Its Compose name is `disa-tomlize-audit`, with loopback ports 28000 (web), 23306 (MySQL), and 28080 (Adminer). Every build context and host bind points inside that directory; fixed container names were removed only in its isolated Compose configuration. The earlier `disa-architecture-audit` stack and host working databases were left intact.

```bash
docker --context desktop-linux compose -p disa-tomlize-audit \
  -f /private/tmp/disa-tomlize-docker-20260906/compose.sandbox.json ps

docker --context desktop-linux compose -p disa-tomlize-audit \
  -f /private/tmp/disa-tomlize-docker-20260906/compose.sandbox.json \
  exec web uv run --locked --offline --group local ./run_tests.py
```

The second command requires the guarded runner's manual `yes`. Automated validation supplied `DISA_DJ__AUTOMATED_TEST_AUTHORIZATION=run-development-tests` only at process startup in these disposable development environments.

Retained evidence includes `minimal-{arm64,amd64}.log`, `final-compiled-build-*.log`, `final-compiled-{arm64,amd64}-tests.log`, `final-runtime-audit.json`, `managed-python-builds.json`, image/container inspection, group-install logs, host test logs, `failure-checks.json`, `rebuild-checks.json`, `browse-comparison.json`, `csv-summary.json`, the actual `browse-portsmouth.csv`, API check results under `stack/code/audit-*.json`, and runtime/restart logs. Experiment scripts and synthetic records live only in that disposable directory, not in this repository. The operating system may eventually clean this directory.

For rollback, retain the prior source and copied settings together with both databases. The verified earlier web image is `sha256:50d378f2c76dee4a4dbf312495ea2a2dc490a4ca5dcc0c65a76a4c22211f96d0`, built from application commit `45bd376b`. Restore the matching source/settings/image without deleting or reinitializing MySQL storage. The newer pre-conversion source is retained in Git at `3b1cb7c8`; retaining live requirements files in the converted checkout is unnecessary.

## User clarifications

> (1) Try 3.8.20 for the uv-install -- but leave `pyproject.toml` as-is.
>
> (2) The question seems to undermine the promised portability of Docker. I believe the devs use Macs -- but this should work on Windows and Linux computers, too. If the Linux support deeply complicates things, let me know.

> Oh -- Mac-intel does not need to be supported.

## Original implementation prompt

Goal: implement the tomlize-docker plan.

Context:

- Review `sr_input_form/REPORT__starting_docker_architecture.md` to understand how docker is currently implemented.

- Review `sr_input_form/PLAN__tomlize_docker.md` to understand the plan.

Tasks:

- implement the `sr_input_form/PLAN__tomlize_docker.md` plan.

- save any decision-notes or assessment-notes or anything else useful to `sr_input_form/REPORT__tomlized_docker_architecture.md`

- Ask me one or two clarifying questions before starting.

- Add this prompt to the bottom of that report.
