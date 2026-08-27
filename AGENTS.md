# AGENTS.md — Repository Agent Instructions (Source of Truth)

This file defines the canonical coding directives for this repository.

If other instruction files exist and conflict with this file, follow this file and treat the others as stale.

## Table of contents

- [Project basics](#project-basics)
- [How to run code](#how-to-run-code)
- [Coding directives (Python)](#coding-directives-python)
- [Django architecture conventions](#django-architecture-conventions)
- [Front-end change guidance](#front-end-change-guidance)
- [Tests](#tests)
- [Change workflow expectations](#change-workflow-expectations)
- [If instructions are missing or ambiguous](#if-instructions-are-missing-or-ambiguous)
- [Agent project index](#agent-project-index)

## Project basics

- Primary language: Python
- Target runtime: Python 3.8, as specified by `pyproject.toml`
- Dependency and execution tool for local and server work: `uv`
- The repository root is the directory containing this file, `.git/`, and `manage.py`.
- Phase 1 keeps the existing pip-based Docker files and requirements unchanged.

## How to run code

- Assume the user is in the repository root.
- Do not activate a virtual environment or source `config/settings_localdev_env.sh` for uv-based work.
- Run a script via: `uv run ./path_to_script.py --help`
- Run tests via: `uv run ./run_tests.py`
- Run a selected test via: `uv run ./run_tests.py disa_app.tests.test_module`
- Run Django management commands via: `uv run ./manage.py THE-COMMAND`
- The outer `../.env` supplies settings for uv-based work.

## Coding directives (Python)

### Type hints and imports

- Use type hints that work on Python 3.8.
- Use `typing.List`, `typing.Dict`, `typing.Optional`, and related forms where built-in generics or `X | None` would require a newer Python.
- Avoid adding imports that are not needed at runtime or for meaningful type clarity.

### Script structure

- Structure runnable modules as:
  - `def main() -> None: ...`
  - `if __name__ == '__main__': main()`
- Keep `main()` simple: parse arguments and coordinate helper functions.
- Put substantive logic into top-level helpers; do not define functions inside other functions.
- Prefer shallow, explicit call paths.

### Functions and control flow

- Prefer a local result and a final return when that improves clarity.
- Do not define functions inside other functions.
- Favor clarity and explicitness over cleverness.

### Logging

- When adding a log statement, when possible, format variable values as a label, followed by a comma and a space, with the value enclosed in double backticks.
- Prefer a label that matches the variable name. For example: ```log.debug(f'branch_and_commit, ``{branch_and_commit}``')```

### HTTP and networking

- The existing application uses `requests`; do not introduce another HTTP library without a documented reason.

### Docstrings

- Use triple-quoted docstrings.
- Write docstrings in present tense, with triple quotes on their own lines.
- End non-test function docstrings with `Called by: the_caller_function()` or the fully qualified caller.
- Start test-function docstring text with `Checks...`.
- For header comments inside functions, start the comment with two hashes.

### Additional coding directives

- Inspect `/ruff.toml` for line length, quote style, and related settings.

### Markdown formatting

- Do not use hard line breaks in Markdown files; let paragraphs wrap naturally.
- When a Markdown file has more than three top-level `##` headings, add a contents list near the top with links to those headings.

## Django architecture conventions

### View-layer responsibilities

- `disa_app/views.py` should contain only view functions that directly handle endpoints listed in `config/urls.py`.
- Views should parse request input, perform minimal validation, delegate substantive work to `disa_app/lib/`, and create the response.

### Business logic placement

- Put domain logic, integrations, and reusable operations in `disa_app/lib/`, not in `disa_app/views.py`.
- Prefer testable functions that accept ordinary Python values rather than Django request objects when practical.

### Imports and dependencies

- Keep view imports limited to needed Django primitives and application helpers.
- Do not create a second collection of business-logic helpers inside `views.py`.

## Front-end change guidance

- Use JavaScript only where it is required.
- Prefer CSS, Python, or Django-template changes when they can provide the requested behavior.

## Tests

- Use Django's test framework.
- Tests are development-only. `run_tests.py` creates separate temporary SQLite databases for Django and SQLAlchemy-backed tests and removes them after the run.
- `config/settings_test.py` replaces Django's normal database with in-memory SQLite and redirects SQLAlchemy when the guarded runner supplies its temporary fixture URL.
- `run_tests.py` displays the configured database targets without credentials. Manual runs require the exact response `yes`; automated development deployments require the exact startup environment value `DISA_DJ__AUTOMATED_TEST_AUTHORIZATION=run-development-tests`.
- Never run the test suite against production data.
- New behavior should usually include a focused success case and at least one failure or edge case.

## Change workflow expectations

1. Read relevant surrounding code and match existing conventions.
2. Make the smallest correct change that satisfies the request.
3. Update tests and run `uv run ./run_tests.py` against the generated test fixtures.
4. If tests cannot run, state the reason and the exact command that remains to be run.

### Commit messages

- Do not commit on your own. Use the bullets below only when asked to prepare commits and commit.
- Group related files into focused commits; do not require a separate commit for every file.
- Keep each commit message brief, with no more than ten words.
- Write messages in the present tense so they complete the phrase "This commit..." Begin with a fitting verb such as "Adds," "Implements," or "Updates."

## If instructions are missing or ambiguous

- Do not ask questions unless necessary to proceed safely.
- Make reasonable assumptions, state them explicitly, and continue.
- If blocked, provide what was tried, what was found, and the smallest concrete next step.

## Agent project index

- `manage.py`: Django command entry point.
- `config/settings.py`: loads the outer `.env` for uv/server work; Docker keeps using the variables supplied by Compose.
- `config/settings_test.py`: replaces Django's database with in-memory SQLite and accepts the temporary SQLAlchemy fixture URL from `run_tests.py`.
- `config/passenger_wsgi.py`: WSGI entry point. It does not parse shell settings after Phase 1.
- `config/urls.py`: endpoint routing.
- `disa_app/views.py`: endpoint handlers.
- `disa_app/lib/`: most application and data-handling logic.
- `disa_app/models.py`: Django-managed user-profile and deletion-marker models.
- `disa_app/models_sqlalchemy.py`: SQLAlchemy mappings for the main historical data.
- `disa_app/settings_app.py`: application settings read from `DISA_DJ__...` environment variables.
- `disa_app/tests/`: Django tests; SQLAlchemy-backed tests use the generated SQLite fixture.
- `disa_app/tests/sqlalchemy_fixture_builder.py`: creates the SQLAlchemy schema and synthetic rows required by tests.
- `disa_app/static/data/`: generated browse and denormalized JSON files; large generated files are ignored.
- `config/requirements_*.txt`: retained for the Phase 1 Docker workflow, not authoritative for uv.
- `pyproject.toml` and `uv.lock`: authoritative dependency declarations for uv-based local and server work.
- The enclosing outer directory contains `.env`, databases, logs, caches, and the deployment caller. Do not copy sensitive outer-directory values into this public repository.
