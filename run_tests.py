#!/usr/bin/env python

"""
Runs Django tests after explicit development-database authorization.

Usage:
    uv run ./run_tests.py
    uv run ./run_tests.py disa_app.tests.test_renamer
"""

import argparse
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO
from urllib.parse import urlsplit

PROJECT_DIR_PATH = Path(__file__).resolve().parent
TEST_SETTINGS_MODULE = 'config.settings_test'
AUTOMATED_TEST_AUTHORIZATION_ENVIRONMENT_KEY = 'DISA_DJ__AUTOMATED_TEST_AUTHORIZATION'
AUTOMATED_TEST_AUTHORIZATION_VALUE = 'run-development-tests'
TEST_SQLALCHEMY_DATABASE_URL_ENVIRONMENT_KEY = 'DISA_DJ__TEST_SQLALCHEMY_DATABASE_URL'
SQLALCHEMY_DATABASE_URL_ENVIRONMENT_KEY = 'DISA_DJ__DATABASE_URL'


def parse_arguments() -> argparse.Namespace:
    """
    Parses optional Django test labels.

    Called by: main()
    """
    parser = argparse.ArgumentParser(
        description=(
            'Runs Django tests after displaying the configured database targets and requiring manual confirmation or '
            'explicit automated authorization. '
            'SQLAlchemy-backed tests use a separate generated SQLite fixture database.'
        ),
    )
    parser.add_argument(
        'test_labels',
        nargs='*',
        help='Optional Django test labels, such as disa_app.tests.test_renamer.',
    )
    arguments = parser.parse_args()
    return arguments


def is_production_hostname(hostname: str) -> bool:
    """
    Returns whether the hostname follows the production naming convention.

    Called by: manage_test_run()
    """
    is_production = hostname.lower().startswith('p')
    return is_production


def load_runtime_environment() -> None:
    """
    Loads test-only Django settings so the database targets can be inspected.

    Called by: manage_test_run()
    """
    os.environ['DJANGO_SETTINGS_MODULE'] = TEST_SETTINGS_MODULE
    import django

    django.setup()


def describe_django_database(database_config: Dict[str, Any]) -> str:
    """
    Returns a credential-free description of a Django database.

    Called by: build_database_warning()
    """
    engine = database_config.get('ENGINE', 'unknown')
    if engine.endswith('sqlite3'):
        configured_name = database_config.get('NAME', '')
        if configured_name == ':memory:':
            description = 'sqlite in-memory database'
        else:
            database_name = Path(configured_name).name or 'unknown-file'
            description = f'sqlite file {database_name}'
    else:
        hostname = database_config.get('HOST') or 'unknown-host'
        database_name = database_config.get('NAME') or 'unknown-database'
        description = f'{engine} at {hostname}/{database_name}'
    return description


def describe_sqlalchemy_database(database_url: str) -> str:
    """
    Returns a credential-free description of the SQLAlchemy database.

    Called by: build_database_warning()
    """
    parsed_url = urlsplit(database_url)
    scheme = parsed_url.scheme or 'unknown-engine'
    if scheme.startswith('sqlite'):
        database_name = Path(parsed_url.path).name or 'unknown-file'
        description = f'sqlite file {database_name}'
    else:
        hostname = parsed_url.hostname or 'unknown-host'
        database_name = Path(parsed_url.path).name or 'unknown-database'
        description = f'{scheme} at {hostname}/{database_name}'
    return description


def build_database_warning() -> str:
    """
    Builds the warning shown before tests are allowed to start.

    Called by: manage_test_run()
    """
    from django.conf import settings

    django_description = describe_django_database(settings.DATABASES['default'])
    sqlalchemy_description = describe_sqlalchemy_database(os.environ[SQLALCHEMY_DATABASE_URL_ENVIRONMENT_KEY])
    warning = (
        '\nWARNING: These tests are for development only.\n'
        'SQLAlchemy-backed tests use a separate generated fixture database.\n'
        f'Django test database: {django_description}\n'
        f'SQLAlchemy test database: {sqlalchemy_description}\n'
        'Both test databases are temporary and are removed after the run.\n'
    )
    return warning


def configure_sqlalchemy_test_database(database_path: Path) -> str:
    """
    Configures the temporary on-disk SQLite URL used by SQLAlchemy-backed tests.

    Called by: manage_test_run()
    """
    database_url = f'sqlite:///{database_path}'
    os.environ[TEST_SQLALCHEMY_DATABASE_URL_ENVIRONMENT_KEY] = database_url
    return database_url


def prepare_sqlalchemy_test_database(database_url: str) -> None:
    """
    Creates the SQLAlchemy schema and inserts the test fixture data.

    Called by: manage_test_run()
    """
    from disa_app.tests.sqlalchemy_fixture_builder import build_database

    build_database(database_url)


def restore_environment_value(key: str, original_value: Optional[str]) -> None:
    """
    Restores or removes an environment value after the temporary test run.

    Called by: manage_test_run()
    """
    if original_value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = original_value


def read_confirmation(warning: str, input_stream: TextIO, output_stream: TextIO) -> bool:
    """
    Displays the warning and returns whether the exact response is yes.

    Called by: request_confirmation()
    """
    output_stream.write(warning)
    output_stream.write('Type yes to run the tests: ')
    output_stream.flush()
    response = input_stream.readline().strip()
    is_confirmed = response == 'yes'
    return is_confirmed


def request_confirmation(warning: str) -> bool:
    """
    Requires the exact response yes through the controlling terminal.

    Called by: request_test_run_authorization()
    """
    is_confirmed = False
    terminal_is_available = True
    try:
        with open('/dev/tty', mode='r+', encoding='utf-8') as terminal:
            is_confirmed = read_confirmation(warning, terminal, terminal)
    except OSError:
        if sys.stdin.isatty() and sys.stderr.isatty():
            is_confirmed = read_confirmation(warning, sys.stdin, sys.stderr)
        else:
            terminal_is_available = False
            print('Tests not run: an interactive terminal is required.', file=sys.stderr)
    if terminal_is_available and not is_confirmed:
        print('Tests not run: the exact response yes was not received.', file=sys.stderr)
    return is_confirmed


def request_test_run_authorization(warning: str, automated_authorization: str) -> bool:
    """
    Accepts exact automated authorization or requests manual confirmation.

    Called by: manage_test_run()
    """
    is_authorized = automated_authorization == AUTOMATED_TEST_AUTHORIZATION_VALUE
    if is_authorized:
        sys.stderr.write(warning)
        print(
            f'Automated test authorization accepted via {AUTOMATED_TEST_AUTHORIZATION_ENVIRONMENT_KEY}.',
            file=sys.stderr,
        )
    else:
        is_authorized = request_confirmation(warning)
    return is_authorized


def run_django_tests(test_labels: List[str]) -> int:
    """
    Runs Django's test command and returns its status.

    Called by: manage_test_run()
    """
    command = [
        sys.executable,
        str(PROJECT_DIR_PATH / 'manage.py'),
        'test',
        f'--settings={TEST_SETTINGS_MODULE}',
    ] + test_labels
    completed_process = subprocess.run(command, cwd=str(PROJECT_DIR_PATH), check=False)
    return completed_process.returncode


def manage_test_run(test_labels: List[str], automated_authorization: str = '') -> int:
    """
    Applies safety checks and runs the requested Django tests.

    Called by: main()
    """
    exit_code = 1
    hostname = socket.gethostname()
    if is_production_hostname(hostname):
        print(f'Tests not run: production hostname detected, ``{hostname}``.', file=sys.stderr)
    else:
        original_test_database_url = os.environ.get(TEST_SQLALCHEMY_DATABASE_URL_ENVIRONMENT_KEY)
        original_database_url = os.environ.get(SQLALCHEMY_DATABASE_URL_ENVIRONMENT_KEY)
        with tempfile.TemporaryDirectory(prefix='disa-sqlalchemy-tests-') as temporary_directory:
            database_path = Path(temporary_directory) / 'DISA-test.sqlite'
            database_url = configure_sqlalchemy_test_database(database_path)
            try:
                load_runtime_environment()
                prepare_sqlalchemy_test_database(database_url)
                warning = build_database_warning()
                if request_test_run_authorization(warning, automated_authorization):
                    exit_code = run_django_tests(test_labels)
            finally:
                restore_environment_value(TEST_SQLALCHEMY_DATABASE_URL_ENVIRONMENT_KEY, original_test_database_url)
                restore_environment_value(SQLALCHEMY_DATABASE_URL_ENVIRONMENT_KEY, original_database_url)
    return exit_code


def main() -> None:
    """
    Parses arguments and coordinates the guarded test run.

    Called by: run_tests.__main__
    """
    automated_authorization = os.environ.get(AUTOMATED_TEST_AUTHORIZATION_ENVIRONMENT_KEY, '')
    arguments = parse_arguments()
    exit_code = manage_test_run(arguments.test_labels, automated_authorization)
    raise SystemExit(exit_code)


if __name__ == '__main__':
    main()
