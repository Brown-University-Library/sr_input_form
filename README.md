# Stolen Relations Django application

## Contents

- [Glossary](#glossary)
- [Installation](#installation)
- [Typical usage](#typical-usage)
- [Checks and tests (optional)](#checks-and-tests-optional)
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

Choose one approach below. Docker sets up the application and its development databases; local uv development requires you to supply the databases yourself. The examples use `sr_input_form_stuff/sr_input_form`; an existing checkout can keep its current directory names.

### Approach 1: Docker development

Install and open Docker Desktop on an Apple Silicon Mac or Windows, or use Docker Engine with Compose on Linux. On Windows, run these commands in a WSL terminal with Docker integration enabled. You also need Git and GitHub SSH access to the repositories, including the private starter-data repository. You do not need to install Python or uv on your computer for this approach.

For a new installation, run these commands in order. If you already have all three repositories together, enter your existing `sr_input_form` directory instead of cloning them again.

```bash
mkdir ./sr_input_form_stuff/
cd ./sr_input_form_stuff/
git clone git@github.com:Brown-University-Library/stolen_relations_start_data.git
git clone --depth 1 git@github.com:Brown-University-Library/sr_dkr_sql-database.git
git clone git@github.com:Brown-University-Library/sr_input_form.git
cd ./sr_input_form/
```

In that same terminal, start the app:

```bash
docker compose up --build
```

**Leave this terminal running.** The command displays logs and does not return a prompt while the app is running. The first build and database setup can take several minutes. Once you see `Starting development server at http://0.0.0.0:8000/`, open <http://127.0.0.1:8000/info/> in your browser. Browse data continues updating in the background, so the logs do not need to become quiet.

Docker creates the working directories and copies `sample_dot_env.txt` to `../docker/.env` if that file is missing. Existing settings and databases are preserved. The sample is ready for the supplied Docker development databases.

Press **Control-C in this terminal when you want to stop the app**. This stops the web app and its supporting services. To run checks or other commands while the app is running, open a second terminal as described below.

### Approach 2: Local development with uv

Use this approach if you want to run Python directly on your computer. You need Git, GitHub SSH access, and [uv](https://docs.astral.sh/uv/getting-started/installation/). Obtain the two development SQLite databases from the team; cloning the code alone does not provide them.

For a new installation, run these commands in order. For an existing checkout, enter its application directory and skip the creation and clone commands.

```bash
mkdir ./sr_input_form_stuff/
cd ./sr_input_form_stuff/
git clone git@github.com:Brown-University-Library/sr_input_form.git
cd ./sr_input_form/
mkdir -p ../DBs ../logs ../cache_dir
cp -n sample_dot_env.txt ../.env
```

The `cp -n` command preserves an existing `.env`. Edit `../.env` before continuing: the shared sample uses Docker's MySQL connection by default. For a local SQLAlchemy SQLite database, replace its `DISA_DJ__DATABASE_URL` assignment with:

```dotenv
DISA_DJ__DATABASE_URL="sqlite:///../DBs/DISA.sqlite"
```

With these paths, place the main application database at `../DBs/DISA.sqlite` and Django's separate database at `../DBs/dj_disa.sqlite`. If your files are elsewhere, update both `DISA_DJ__DATABASE_URL` and `DISA_DJ__DATABASES_JSON` accordingly. Review the remaining settings for your installation.

Then install the dependencies:

```bash
uv sync --locked --group local
```

After it finishes, start the app in the same terminal:

```bash
uv run ./manage.py runserver
```

Leave this terminal running and open <http://127.0.0.1:8000/info/>. Press **Control-C** here to stop the server. If you want to run other commands while it runs, use a second terminal.

### Where settings live

Docker uses `../docker/.env`; local uv development uses `../.env`. These are separate files outside the application Git repository. Editing the sample does not change either existing settings file.

## Typical usage

All commands below run from your application directory, `sr_input_form/`.

### Starting and stopping

For Docker, start a later development session with:

```bash
docker compose up
```

For local uv development, use:

```bash
uv run ./manage.py runserver
```

Each command keeps its terminal occupied. Leave it running while you work in your editor and browser; press Control-C in that terminal when finished. Python code changes normally reload the server automatically. Refresh the browser to see page changes.

For ordinary Docker sessions, Control-C followed later by `docker compose up` reuses the existing containers and databases. Avoid `docker compose down` as a routine stop command: it removes containers, and this setup does not guarantee that a newly created MySQL container will reuse the edited database.

### After changing settings or dependencies

After editing `../docker/.env`, leave Docker running in the first terminal and run this in a **second terminal**, from the application directory:

```bash
docker compose restart web
```

For local uv settings changes, stop the server with Control-C, then run `uv run ./manage.py runserver` again in that terminal.

After pulling changes that update Python dependencies, stop the app with Control-C. For Docker, restart with `docker compose up --build`. For local uv development, run `uv sync --locked --group local`, wait for it to finish, then run `uv run ./manage.py runserver`.

### Other useful pages

With the app running, the login page is <http://127.0.0.1:8000/login/> and version information is at <http://127.0.0.1:8000/version/>.

For Docker's database viewer, open <http://127.0.0.1:8080/>. Use server `db`, database `stolenrelations`, username `user`, and password `user` for the example setup.

## Checks and tests (optional)

These checks are useful after setup or code changes. Choose the commands for your installation method.

### Docker: use a second terminal

**Keep `docker compose up` running in the first terminal. Open a second terminal or tab**, then enter the same application directory. Replace `/path/to/` below with the actual location of your enclosing directory.

Run these commands one after another; each returns to the prompt when it finishes:

```bash
cd /path/to/sr_input_form_stuff/sr_input_form/
docker compose exec web uv run --locked --offline --group local ./manage.py check
docker compose exec web uv run --locked --offline --group local ./run_tests.py
```

The test command pauses for confirmation: type `yes` and press Enter. A successful test run ends with `OK`. The app keeps running in the first terminal.

If you see **`service "web" is not running`**, return to the first terminal, run `docker compose up`, and wait for the server to start. Then retry the check in the second terminal. Cancelling `docker compose up` stops the service that `docker compose exec` needs.

### Local uv development

If `uv run ./manage.py runserver` is running, **open a second terminal** and enter the same application directory. Otherwise, use your current terminal there. Run:

```bash
uv run ./manage.py check
uv run ./run_tests.py
```

Type `yes` and press Enter when the test runner asks. You can also run a single test module:

```bash
uv run ./run_tests.py disa_app.tests.test_renamer
```

Both installation methods use the guarded `run_tests.py` runner, which creates temporary test databases. Use it instead of `manage.py test`. The existing `caches.W003` warning about a relative cache directory may appear during checks; it does not prevent the tests from running.

## Dependency and settings conventions

`pyproject.toml` and `uv.lock` define the Python dependencies. Docker supplies Python 3.8.20; local Python must satisfy the declared Python 3.8 range. Update the lockfile along with dependency changes before rebuilding. Application settings are loaded from the selected `.env`, and file values override inherited application settings.

For the detailed Docker design, platform checks, and known limitations, see the [implementation report](REPORT__tomlized_docker_architecture.md).

If an existing checkout still uses the former GitHub repository address, update it from that checkout's application directory:

```bash
git remote set-url origin git@github.com:Brown-University-Library/sr_input_form.git
```

## Notes for those of us who don't know Django

Some critical files:

### [sr_input_form/config/settings.py](https://github.com/Brown-University-Library/sr_input_form/blob/main/config/settings.py)

Django settings for sr_input_form. Mostly "where are things" and security keys, etc.

Generated by 'django-admin startproject' using Django 1.11.

[More information on this file](https://docs.djangoproject.com/en/3.2/topics/settings/)

[Full list of settings and their values](https://docs.djangoproject.com/en/3.2/ref/settings/)

### [sr_input_form/config/urls.py](https://github.com/Brown-University-Library/sr_input_form/blob/main/config/urls.py)

Maps URL patterns to views, e.g.:

```
url( r'^source/(?P<src_id>.*)/$', views.source, name='source_url' )
```

which maps to the function definition in [sr_input_form/disa_app/views.py](https://github.com/Brown-University-Library/sr_input_form/blob/main/disa_app/views.py):

```
def source( request, src_id ):
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

Django models for users' application profiles and deletion markers.

### [sr_input_form/disa_app/settings_app.py](https://github.com/Brown-University-Library/sr_input_form/tree/main/disa_app/settings_app.py)

Application-specific settings, including authentication and the SQLAlchemy database URL. Django loads the `.env` in `config/settings.py`; this module reads application values from that environment.

### [sr_input_form/disa_app/views.py](https://github.com/Brown-University-Library/sr_input_form/tree/main/disa_app/views.py)

A bunch of routines that are called by `sr_input_form/config/urls.py` and reference `sr_input_form/disa_app/disa_app_templates`.
