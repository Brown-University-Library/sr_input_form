# Stolen Relations Django application

## Contents

- [Glossary](#glossary)
- [Installation](#installation)
- [Typical usage](#typical-usage)
- [Running tests with uv](#running-tests-with-uv)
- [Phase 1 dependency note](#phase-1-dependency-note)
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

There are two supported approaches for running the Python application during Phase 1. Developers using Docker can continue with the existing Docker setup. Developers running Python directly on the host can use uv and the outer `.env` file.

### Approach 1: Docker-based development

(Assumes [Docker](https://www.docker.com) is installed and running.)

- Create a local "stuff" directory (name it anything) -- and from your terminal, cd into it (one-time step)


From the terminal, run:

- `git clone git@github.com:Brown-University-Library/stolen_relations_start_data.git`<br />_(a one-time step; downloads the login/password security information for the input form)_
- `git clone --depth 1 git@github.com:Brown-University-Library/sr_dkr_sql-database.git`<br/>_(a one-time step; downloads the SR mySQL database)_
- `git clone git@github.com:Brown-University-Library/sr_input_form.git`<br/>_(a one-time step; downloads the SR input form codebase)_
- `cd sr_input_form`<br />_Sets the current directory to sr\_input\_form_
- `docker-compose up`<br />_Creates the container (which starts the webapp)_

The webapp should be running; from a browser, go to `http://127.0.0.1:8000/version/` or `http://127.0.0.1:8000/login/`. 

If you want to tinker with the database via the database manager _adminer_, go to `http://127.0.0.1:8080`.

### Approach 2: Host-based development with uv

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

The real `.env` belongs in `sr_input_form_stuff/`, one directory above this Git repository. It may contain local sensitive values because the outer directory is not tracked by this repository. The Django and SQLAlchemy settings are independent; each must point to the intended host-accessible development database.

Install the locked local dependencies and verify Django:

```bash
uv sync --locked --group local
uv run ./manage.py check
```

Start the development server:

```bash
uv run ./manage.py runserver
```

For this approach, do not activate a virtual environment, set `DISA_DJ__ENV_SETTINGS_PATH`, or source `config/settings_localdev_env.sh`. Django loads `../.env` through `python-dotenv`.

## Typical usage

### Docker

- `cd <SOME_PATH>/sr_input_form`<br />_Sets the current directory to sr\_input\_form_
- `docker-compose up`<br />_Creates the container (which starts the webapp)_

Note: if a code-update installs a new python-package, either:

- delete the `sr\_input\_form-web` image which should force it to be rebuilt (best option), **or...**    
- run `docker-compose up --build` to force the container to be rebuilt. (I don't think this actually creates a new image, so subsequent runs of `docker-compose up` will still use the old image.)

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

## Phase 1 dependency note

Host-based development and the new server deployment path use `pyproject.toml`, `uv.lock`, and uv. During Phase 1, Docker continues to use the existing pip requirements files and does not consume `pyproject.toml` or `uv.lock`. Moving Docker to uv is deferred to Phase 2.

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
