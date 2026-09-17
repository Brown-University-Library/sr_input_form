"""
Django settings used only by the test runner.

The application reads its historical data through SQLAlchemy, so that database
comes from the temporary URL supplied by run_tests.py when available. Django-managed
test tables use a separate in-memory SQLite database. Neither database requires
MySQL database-creation permission.
"""

import os

from .settings import *

TEST_SQLALCHEMY_DATABASE_URL_KEY = 'DISA_DJ__TEST_SQLALCHEMY_DATABASE_URL'
if TEST_SQLALCHEMY_DATABASE_URL_KEY in os.environ:
    os.environ['DISA_DJ__DATABASE_URL'] = os.environ[TEST_SQLALCHEMY_DATABASE_URL_KEY]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}
