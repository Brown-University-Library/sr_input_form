"""
Checks creation of the isolated SQLAlchemy fixture database.
"""

import tempfile
from pathlib import Path

from django.test import SimpleTestCase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from disa_app import models_sqlalchemy as models_alch
from disa_app.tests.sqlalchemy_fixture_builder import AGE_CATEGORIES, build_database


class SqlalchemyFixtureBuilderTest(SimpleTestCase):
    """
    Checks fixture creation and its safety restriction.
    """

    def test_build_database_populates_required_rows(self):
        """
        Checks that a fresh SQLite fixture contains stable IDs and relationships.
        """
        with tempfile.TemporaryDirectory(prefix='disa-fixture-builder-test-') as temporary_directory:
            database_path = Path(temporary_directory) / 'fixture.sqlite'
            database_url = f'sqlite:///{database_path}'
            build_database(database_url)

            engine = create_engine(database_url)
            session_factory = sessionmaker(bind=engine)
            session = session_factory()
            try:
                self.assertIsNotNone(session.query(models_alch.Citation).get(1))
                self.assertIsNotNone(session.query(models_alch.Reference).get(49))
                self.assertIsNotNone(session.query(models_alch.Referent).get(2033))
                self.assertIsNotNone(session.query(models_alch.User).get(1))
                self.assertEqual(len(AGE_CATEGORIES), session.query(models_alch.AgeCategory).count())
                self.assertIsNotNone(
                    session.query(models_alch.ReferentRelationship)
                    .filter_by(
                        subject_id=3703,
                        object_id=3704,
                        role_id=7,
                    )
                    .first()
                )
                self.assertIsNone(
                    session.query(models_alch.ReferentRelationship)
                    .filter_by(
                        subject_id=3703,
                        object_id=3704,
                        role_id=8,
                    )
                    .first()
                )
            finally:
                session.close()
                engine.dispose()

    def test_build_database_rejects_non_sqlite_url(self):
        """
        Checks that the fixture builder refuses a non-SQLite target.
        """
        with self.assertRaisesRegex(ValueError, 'must use SQLite'):
            build_database('mysql+pymysql://example.invalid/test')
