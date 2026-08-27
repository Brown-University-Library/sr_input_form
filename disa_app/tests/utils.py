"""
Provides shared support for tests that access the SQLAlchemy database.
"""

from unittest import skipUnless
from urllib.parse import urlsplit

from disa_app import settings_app

SQLALCHEMY_USES_SQLITE = urlsplit(settings_app.DB_URL).scheme.startswith('sqlite')

# Direct Django test commands do not build the isolated SQLAlchemy fixture.
# Keep data-dependent tests away from a configured MySQL database.
skip_unless_sqlalchemy_sqlite = skipUnless(
    SQLALCHEMY_USES_SQLITE,
    'Requires the isolated SQLAlchemy SQLite fixture created by run_tests.py.',
)
