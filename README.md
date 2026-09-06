# Stolen Relations Django application

## Contents

- [Glossary](#glossary)
- [Installation](#installation)
- [Typical usage](#typical-usage)
- [Running tests with uv](#running-tests-with-uv)
- [Dependency and settings conventions](#dependency-and-settings-conventions)
- [Notes for those of us who don't know Django](#notes-for-those-of-us-who-dont-know-django)

## Glossary

Note: _Over the course of the project, the terminology has changed, with the result that different areas of the codebase use different names for the same concepts._ 

While we aspire to eventually to update for consistency, in the meantime, these three terms listed below are used interchangeably in code. The first listed option (in bold) is the one currently used by the project, and the term used in the database is indicated by `db`:

- **source** / citation `db`<br />
  The document that contains the Records. A Source includes bibliographic information (e.g. author, title, ...)
- **record** / item / reference `db`<br />
  The bit of text within the Source that describes a group of Referents (references to people) as well as an event or situation with date, location, etc. Typical Record types include self-emancipation notices (aka "Escape Slave ads") or a single baptismal record
- **referent** `db` / person / entrant<br />
  A reference to a person contained in a Record. Note that we reserve the term _Person_ to indicate a particular individual. There may be multiple references to the same Person across different Records, and therefore there may be multiple Referents that in fact are the same Person

## Installation

The repository is [Brown-University-Library/sr_input_form](https://github.com/Brown-University-Library/sr_input_form). Examples use the default clone directory `sr_input_form/`. For an existing checkout, enter its actual directory; changing the remote URL does not require renaming that directory. To update an existing checkout's remote, run this from its Git root:

```bash
git remote set-url origin git@github.com:Brown-University-Library/sr_input_form.git
```

Docker, host development, and server deployments all use `pyproject.toml`, `uv.lock`, and uv. Application settings are loaded by `python-dotenv` from the `.env` one directory above the code.

### Approach 1: Docker development

Install and start Docker with Linux-container support: Docker Desktop on Apple Silicon Macs or Windows (normally WSL 2), or Docker Engine with the Compose plugin on Linux. No host Python or uv installation is required. The web image supports Linux ARM64 and AMD64; Docker selects the architecture automatically. Intel Macs are outside the required support scope. On Windows, use a WSL terminal for these commands and preferably keep the checkout in the WSL filesystem. Allow Docker access to the enclosing directory when prompted. The startup commands run in Bash inside the Linux container.

The examples use `sr_input_form_stuff` for the enclosing directory; existing installations can keep their current directory name. Create that enclosing directory, then clone the three repositories as siblings. Access to the private starter-data repository is required:

```bash
mkdir sr_input_form_stuff
cd sr_input_form_stuff
git clone git@github.com:Brown-University-Library/stolen_relations_start_data.git
git clone --depth 1 git@github.com:Brown-University-Library/sr_dkr_sql-database.git
git clone git@github.com:Brown-University-Library/sr_input_form.git
cd sr_input_form
```

Start Docker with the supplied development defaults:

```bash
docker compose up --build
```

Compose creates `DBs/`, `logs/`, `cache_dir/`, and `docker/` in the enclosing directory as needed. On first startup, the web container copies `sample_dot_env.txt` to `../docker/.env`. Existing settings are preserved. To customize them, edit `../docker/.env` and run `docker compose restart web`. You can also supply that file before the first startup.

Keep the example SQLAlchemy URL pointed to service `db:3306` and its development credentials aligned with MySQL's `MYSQL_*` values in Compose. Django separately uses `../DBs/dj_disa.sqlite`. Keep browse proxy URLs on internal port 8000 even if you change a published host port. The example identities and passwords are for development; use the team's supplied seed account or create an account with the appropriate application profile.

The `web.command` block in `docker-compose.yml` checks the mounted dependency declarations offline, waits up to 180 seconds for MySQL's TCP port, copies missing SQLite and browse seed files, launches browse generation, and starts Django. It preserves existing working files. Starter files are `dj_disa.db`, `browse.json`, and `browse_formatted.json`; the companion MySQL build needs `sr_inserts_together.sql`. No automatic migrations or account creation run.

Once you see the terminal activity stop, showing `django-web-container  | starting info()`, open <http://127.0.0.1:8000/info/> or <http://127.0.0.1:8000/version/> or <http://127.0.0.1:8000/login/>. Adminer is at <http://127.0.0.1:8080/>: server `db`, database `stolenrelations`, user/password `user`/`user` for the example setup.

Compose mounts only the application checkout, DBs, logs, cache directory, read-only starter data, and the writable Docker settings directory. Inside the image, `/sr_project_stuff/.env` points to `/sr_project_stuff/docker/.env`; Python parses the file created in that mounted directory. The host/server `../.env` stays separate. MySQL's entrypoint still receives its own `MYSQL_*` values from Compose.

### Approach 2: Local development with uv

(This installs only the code. Manual sqlite-dbs will need to be installed and referenced in the `.env`.)

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if it is not already available. Then enter the Git repository from the enclosing outer directory:

```bash
cd /path/to/sr_input_form_stuff/
git clone git@github.com:Brown-University-Library/sr_input_form.git
cd ./sr_input_form/
```

Create the outer environment file once, then review every value and path before running the application:

```bash
cp sample_dot_env.txt ../.env
```

The shared sample uses Docker's MySQL connection by default. For local SQLite use, edit the copied `../.env` and replace its `DISA_DJ__DATABASE_URL` assignment with:

```dotenv
DISA_DJ__DATABASE_URL="sqlite:///../DBs/DISA.sqlite"
```

Adjust the path to your existing SQLAlchemy database. Django's separate database path remains in `DISA_DJ__DATABASES_JSON`; provide both databases before starting the application.

Reminder: the real `.env` belongs in `sr_input_form_stuff/`, one directory above the Git repository. It may contain local sensitive values because the outer directory is not tracked by this repository. The Django and SQLAlchemy settings are independent; each must point to the intended host-accessible development database.

Install the locked local dependencies and verify Django:

```bash
uv sync --locked --group local
uv run ./manage.py check
```

Start the development server:

```bash
uv run ./manage.py runserver
```


## Typical usage

### Docker

From the application directory:

```bash
docker compose up
docker compose exec web uv run --locked --offline --group local ./manage.py check
docker compose exec web uv run --locked --offline --group local ./run_tests.py
```

The test command prompts for the exact response `yes` and uses temporary fixture databases. Source edits retain Django autoreload. After dependency changes, update `uv.lock` and run `docker compose up --build`; this builds and uses the updated image. If startup reports a stale lock or an unavailable dependency, resolve/update the lock with uv and rebuild. Startup does not download Python or packages. A Docker-only developer can update the lock using the existing image with `docker compose run --rm --no-deps web uv lock`, then rebuild.

After editing `../docker/.env`, run `docker compose restart web` to reload settings. For an IDE attached to the running container, select `/opt/venv/bin/python`; the underlying managed interpreter remains at `/opt/python`. A host `.venv` is not used inside Docker.

Browse generation runs asynchronously at startup. Check `docker compose logs web` and the newly written JSON completion metadata before assuming it succeeded. Once that startup job finishes, a foreground refresh can be run with:

```bash
docker compose exec web uv run --locked --offline --group local disa_app/lib/generate_browse_data.py
```

Use `docker compose stop` and `docker compose start` to preserve the current containers. MySQL still uses the companion image's anonymous data volume: `down` followed by `up` does not guarantee reconnection to the edited database. Back up both MySQL and Django SQLite before container replacement or rollback; this migration does not change that existing storage behavior. The companion backup script is available through `docker compose exec db /usr/local/bin/sr-db-backup.sh`.

### uv

From `sr_input_form/`, with the outer `.env` already reviewed:

```bash
uv sync --locked --group local
uv run ./manage.py runserver
```


## Running tests with uv

Tests are for development environments only. The guarded runner uses `config/settings_test.py`, which replaces the normal Django database with a temporary in-memory SQLite database. It also creates a temporary on-disk SQLite database for SQLAlchemy-backed tests and populates it with synthetic fixture data.

The runner redirects `DISA_DJ__DATABASE_URL` to that generated fixture before application modules load. Both test databases are removed after the run, including after test failure. The configured local or server SQLAlchemy database is not modified.

Run the full Django test suite with:

```bash
uv run ./run_tests.py
```

Or pass a Django test label to run a selected test module, class, or method:

```bash
uv run ./run_tests.py disa_app.tests.test_renamer
```

The runner displays credential-free descriptions of both database targets. For a manual run, tests start only after the developer types the exact lowercase response `yes`. The runner refuses to start on a production hostname beginning with `p`.

An automated development deployment can run without a terminal when its caller explicitly exports `DISA_DJ__AUTOMATED_TEST_AUTHORIZATION=run-development-tests`. The runner reads this authorization before loading the outer `.env`; keep it in the deployment caller rather than adding it to `.env`. The production-hostname refusal still applies when automated authorization is present.

Do not use a plain `uv run ./manage.py test` for this application. That command uses the normal MySQL settings and asks MySQL to create a test database. The direct Django equivalent is `uv run ./manage.py test --settings=config.settings_test`, but it does not build or select the isolated SQLAlchemy fixture. Reserve it for tests known not to access SQLAlchemy.

## Dependency and settings conventions

`pyproject.toml` and `uv.lock` are the only maintained Python dependency declarations. Keep the shared Python range `>=3.8,<3.9`; Docker installs exactly 3.8.20 through pinned uv on pinned Debian. Host and server interpreters may use any patch allowed by that range. Docker selects Python through `UV_PYTHON=3.8.20`; `uv sync --locked` checks TOML compatibility and lock freshness and synchronizes the environment during build/startup. This does not make the shared TOML range an exact patch pin.

Docker installs runtime dependencies plus the `local` group. Host development uses `uv sync --locked --group local`; development servers use `--group staging`; production uses `--group prod`, which adds `mysqlclient==2.1.1` and needs the server's MySQL build prerequisites. Never install all groups just to make development work. Existing package pins remain unchanged.

Every workflow requires the `.env` one directory above its code. File values override conflicting inherited application variables (`override=True`), and missing required settings fail explicitly. The Docker source file is `../docker/.env`; the host/server source file is `../.env`. Keep real settings files outside Git. Quoted JSON is supported, empty assignments produce empty strings, and `${NAME}` is expanded by python-dotenv; account for interpolation when choosing values. Compose mounts the Docker settings directory and does not also parse its `.env` as a service `env_file`.

## Notes for those of us who don't know Django

Some critical files:

### [sr_input_form/config/settings.py](https://github.com/Brown-University-Library/sr_input_form/blob/main/config/settings.py)

Django settings for sr_input_form. Mostly "where are things" and security keys, etc.

Generated by 'django-admin startproject' using Django 1.11.

[More information on this file](https://docs.djangoproject.com/en/1.11/topics/settings/)

[Full list of settings and their values](https://docs.djangoproject.com/en/1.11/ref/settings/)

### [sr_input_form/config/urls.py](https://github.com/Brown-University-Library/sr_input_form/blob/main/config/urls.py)

Maps URL patterns to views, e.g.:

```
url( r'^editor/documents/(?P<cite_id>.*)/$', views.edit_citation, name='edit_citation_url' )
```

which maps to the function definition in [sr_input_form/disa_app/views.py](https://github.com/Brown-University-Library/sr_input_form/blob/main/disa_app/views.py):

```
@shib_login
def edit_citation( request, cite_id=None ):
```

### [sr_input_form/disa_app/admin.py](https://github.com/Brown-University-Library/sr_input_form/blob/main/disa_app/admin.py)

Seems to extend administrative functions, and handles the "marked for deletion" system. Contains 3 class definitions:

- MarkedForDeletionAdminForm
- UserProfileAdmin
- MarkedForDeletionAdmin

### [sr_input_form/disa_app/disa_app_templates](https://github.com/Brown-University-Library/sr_input_form/tree/main/disa_app/disa_app_templates)

The templates for the public pages. These files are referenced in `disa_app/views.py`.

### [sr_input_form/disa_app/lib](https://github.com/Brown-University-Library/sr_input_form/tree/main/disa_app/lib)

A bunch of Stolen Relations-specific python code. This seems to be the main code area. 

Includes:

- `generate_browse_data.py`
- a bunch of `view_*_manager.py`

### [sr_input_form/disa_app/models_sqlalchemy.py](https://github.com/Brown-University-Library/sr_input_form/tree/main/disa_app/models_sqlalchemy.py)

Model definition for SQL Alchemy

### [sr_input_form/disa_app/models.py](https://github.com/Brown-University-Library/sr_input_form/tree/main/disa_app/models.py)

Not sure (ask Birkin)

### [sr_input_form/disa_app/settings_app.py](https://github.com/Brown-University-Library/sr_input_form/tree/main/disa_app/settings_app.py)

Some random settings—authentication, DB location, etc. Not sure how this relates to `sr_input_form/config/settings.py`

### [sr_input_form/disa_app/views.py](https://github.com/Brown-University-Library/sr_input_form/tree/main/disa_app/views.py)

A bunch of routines that are called by `sr_input_form/config/urls.py` and reference `sr_input_form/disa_app/disa_app_templates`.
