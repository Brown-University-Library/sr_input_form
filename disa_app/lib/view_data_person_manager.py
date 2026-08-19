# -*- coding: utf-8 -*-

import json
import logging

from sqlalchemy import create_engine

from disa_app import settings_app


log = logging.getLogger(__name__)


def link_referents(referent_uuid_1: str, referent_uuid_2: str, by_value: str, note: str) -> dict:
    """Unifies two referents into the same person via the database stored procedure."""
    log.debug('starting link_referents()')
    engine = create_engine(settings_app.DB_URL, echo=False)
    connection = engine.raw_connection()
    cursor = None
    try:
        cursor = connection.cursor()

        log.exception('BOOYAH')
        cursor.callproc(
            'Unify_referentsToSamePerson',
            [referent_uuid_1, referent_uuid_2, by_value, note],
        )
        person_uuid = None
        for result in cursor.stored_results():
            rows = result.fetchall()
            if rows:
                person_uuid = rows[0][0]
                break
        connection.commit()
        return {'person_uuid': person_uuid}
    except Exception:
        connection.rollback()
        log.exception('problem calling Unify_referentsToSamePerson')
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
