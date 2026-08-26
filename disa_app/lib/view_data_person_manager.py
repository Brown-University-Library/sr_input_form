# -*- coding: utf-8 -*-

import json
import logging

from sqlalchemy import create_engine

from disa_app import settings_app


log = logging.getLogger(__name__)


GET_ALL_PEOPLE_SQL = """
    SELECT
        people.uuid AS person_uuid,
        referents.uuid AS referent_uuid,
        referent_names.first AS referent_first_name,
        referent_names.last AS referent_last_name
    FROM `1_people` AS people
    LEFT JOIN `6_is_person` AS person_referents
        ON person_referents.person_uuid = people.uuid
    LEFT JOIN `5_referents` AS referents
        ON referents.uuid = person_referents.referent_uuid
    LEFT JOIN `6_referent_names` AS referent_names
        ON referent_names.id = referents.primary_name_id
    WHERE people.resolved_person_uuid IS NULL
    ORDER BY people.uuid, referents.uuid
"""


def get_all_people() -> dict:
    """Gets all people and their linked referents using one SQL statement."""
    log.debug('starting view_data_person_manager.get_all_people()')
    engine = create_engine(settings_app.DB_URL, echo=False)
    connection = engine.raw_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(GET_ALL_PEOPLE_SQL)
        rows = cursor.fetchall()

        people_by_uuid = {}
        for person_uuid, referent_uuid, first_name, last_name in rows:
            if person_uuid not in people_by_uuid:
                people_by_uuid[person_uuid] = {
                    'person_uuid': person_uuid,
                    'referents': [],
                }

            if referent_uuid is not None:
                referent_name = ' '.join(
                    part.strip()
                    for part in (first_name, last_name)
                    if part and part.strip()
                )
                people_by_uuid[person_uuid]['referents'].append({
                    'referent_uuid': referent_uuid,
                    'name': referent_name,
                })

        return {'people': list(people_by_uuid.values())}
    except Exception:
        connection.rollback()
        log.exception('problem getting all people')
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def link_referents(referent_uuid_1: str, referent_uuid_2: str, by_value: str, note: str) -> dict:
    """Unifies two referents into the same person via the database stored procedure."""
    log.debug('starting view_data_person_manager.link_referents()')
    engine = create_engine(settings_app.DB_URL, echo=False)
    connection = engine.raw_connection()
    cursor = None
    try:
        cursor = connection.cursor()

        log.debug('calling Unify_referentsToSamePerson')
        cursor.callproc(
            'Unify_referentsToSamePerson',
            [referent_uuid_1, referent_uuid_2, by_value, note],
        )
        person_uuid = None

        while True:
            if cursor.description is not None:
                rows = cursor.fetchall()
                log.debug('rows = %s', rows)
            else:
                rows = ()

            if person_uuid is None and rows:
                person_uuid = rows[0][0]

            if not cursor.nextset():
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


def unlink_referent(referent_uuid: str, by_value: str, note: str) -> dict:
    """Unlinks a referent from a person via the database stored procedure."""
    log.debug('starting unlink_referent()')
    engine = create_engine(settings_app.DB_URL, echo=False)
    connection = engine.raw_connection()
    cursor = None
    try:
        cursor = connection.cursor()

        log.exception('BOOYAH')
        cursor.callproc(
            'Unify_unlinkReferentFromPerson',
            [referent_uuid, by_value, note],
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
        log.exception('problem calling Unify_unlinkReferentFromPerson')
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
