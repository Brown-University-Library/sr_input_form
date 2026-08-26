"""
Django settings used only by the test runner.

The application reads its historical data through SQLAlchemy, so that database
continues to come from DISA_DJ__DATABASE_URL. Django-managed test tables use a
separate in-memory SQLite database and never require MySQL database-creation
permission.
"""

from .settings import *  # noqa: F401,F403


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}
