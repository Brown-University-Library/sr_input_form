"""
Provides shared support for tests that access the SQLAlchemy database.
"""

from unittest import skipUnless
from urllib.parse import urlsplit

from disa_app import settings_app

SQLALCHEMY_USES_SQLITE = urlsplit(settings_app.DB_URL).scheme.startswith('sqlite')

# TODO: Remove this temporary decorator after the affected tests create all of
# their SQLAlchemy data and can safely clean it up on both SQLite and MySQL.
skip_unless_sqlalchemy_sqlite = skipUnless(
    SQLALCHEMY_USES_SQLITE,
    'TODO: create isolated SQLAlchemy test data before enabling this test against MySQL.',
)
