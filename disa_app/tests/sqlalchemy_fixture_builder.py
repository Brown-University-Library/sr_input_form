"""
Builds the isolated SQLAlchemy database used by the Django test suite.
"""

import datetime
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from disa_app import models_sqlalchemy as models_alch

AGE_CATEGORIES = (
    ('78ac411b-be39-41e3-be66-43017e30d105', 'Infant'),
    ('761cc55d-8bf6-4737-a728-30f20c4d66b2', 'Child'),
    ('3a592293-9d21-4cef-968a-fcebfd1c0835', 'Adult'),
)

CITATION_TYPES = (
    (20, 'Book', 5, 'book'),
    (21, 'Book Section', 6, 'bookSection'),
    (26, 'Document', 11, 'document'),
    (33, 'Interview', 18, 'interview'),
    (34, 'Journal Article', 19, 'journalArticle'),
    (36, 'Magazine Article', 21, 'magazineArticle'),
    (37, 'Manuscript', 22, 'manuscript'),
    (39, 'Newspaper Article', 24, 'newspaperArticle'),
    (46, 'Thesis', 31, 'thesis'),
    (49, 'Webpage', 34, 'webpage'),
)


def build_database(database_url: str) -> None:
    """
    Creates and populates a fresh SQLite database for SQLAlchemy-backed tests.

    Called by: run_tests.prepare_sqlalchemy_test_database()
    """
    parsed_url = urlsplit(database_url)
    if not parsed_url.scheme.startswith('sqlite'):
        raise ValueError('The SQLAlchemy test fixture database must use SQLite.')

    engine = create_engine(database_url)
    models_alch.Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        seed_zotero_and_citation_data(session)
        seed_reference_lookups(session)
        seed_references(session)
        seed_referents_and_relationships(session)
        seed_audit_user(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def seed_zotero_and_citation_data(session: Session) -> None:
    """
    Adds citation types, Zotero form fields, and required citations.

    Called by: build_database()
    """
    zotero_fields = [
        models_alch.ZoteroField(id=30, name='date', display_name='Date'),
        models_alch.ZoteroField(id=67, name='pages', display_name='Pages'),
        models_alch.ZoteroField(id=94, name='shortTitle', display_name='Short Title'),
        models_alch.ZoteroField(id=100, name='title', display_name='Title'),
    ]
    session.add_all(zotero_fields)

    template_id = 1
    for citation_type_id, citation_type_name, zotero_type_id, zotero_type_name in CITATION_TYPES:
        zotero_type = models_alch.ZoteroType(
            id=zotero_type_id,
            name=zotero_type_name,
            creator_name='author',
        )
        citation_type = models_alch.CitationType(
            id=citation_type_id,
            name=citation_type_name,
            zotero_type=zotero_type,
        )
        session.add_all([zotero_type, citation_type])
        for field_id, rank in ((100, 0), (30, 5), (94, 10)):
            session.add(
                models_alch.ZoteroTypeField(
                    id=template_id,
                    zotero_type_id=zotero_type_id,
                    zotero_field_id=field_id,
                    rank=rank,
                )
            )
            template_id += 1

    citations = [
        models_alch.Citation(
            id=1,
            citation_type_id=20,
            display='Test citation one',
            comments='',
            acknowledgements='',
        ),
        models_alch.Citation(
            id=768,
            citation_type_id=26,
            display='Test citation for record creation',
            comments='',
            acknowledgements='',
        ),
        models_alch.Citation(
            id=992,
            citation_type_id=20,
            display='Test citation for the redesign page',
            comments='',
            acknowledgements='',
        ),
    ]
    session.add_all(citations)
    session.add_all(
        [
            models_alch.CitationField(citation_id=1, field_id=100, field_data='Test citation one'),
            models_alch.CitationField(citation_id=992, field_id=100, field_data='Test redesign citation'),
        ]
    )
    session.flush()


def seed_reference_lookups(session: Session) -> None:
    """
    Adds lookup rows used while creating and editing records and referents.

    Called by: build_database()
    """
    session.add_all(
        [
            models_alch.ReferenceType(id=1, name='Baptism'),
            models_alch.ReferenceType(id=13, name='Unspecified'),
            models_alch.ReferenceType(id=20, name='Petition to Assembly'),
            models_alch.ReferenceType(id=29, name='Burial Record'),
        ]
    )
    session.add_all(
        [
            models_alch.NationalContext(id=1, name='British'),
            models_alch.NationalContext(id=2, name='American'),
            models_alch.NationalContext(id=3, name='French'),
            models_alch.NationalContext(id=4, name='Spanish'),
        ]
    )
    session.add_all(
        [
            models_alch.LocationType(id=1, name='Colony/State'),
            models_alch.LocationType(id=3, name='Locale'),
            models_alch.LocationType(id=4, name='City'),
        ]
    )
    session.add_all(
        [
            models_alch.Location(id=21, name='Boston'),
            models_alch.Location(id=23, name='New York'),
            models_alch.Location(id=357, name='somewhere about Pumpkin-Hill'),
            models_alch.Location(id=630, name='Rhode Island'),
            models_alch.Location(id=735, name='Massachusetts'),
            models_alch.Location(id=748, name='Albany'),
        ]
    )
    session.add(models_alch.NameType(id=7, name='Given'))
    session.add_all([models_alch.AgeCategory(uuid=uuid, name=name) for uuid, name in AGE_CATEGORIES])
    session.add_all(
        [
            models_alch.Role(id=1, name='Enslaved', name_as_relationship='enslaved by'),
            models_alch.Role(id=2, name='Owner', name_as_relationship='owner of'),
            models_alch.Role(id=3, name='Priest', name_as_relationship='priest for'),
            models_alch.Role(id=7, name='Shipped', name_as_relationship='shipped by'),
            models_alch.Role(id=8, name='Arrived', name_as_relationship='delivered by'),
            models_alch.Role(id=30, name='Previous Owner', name_as_relationship=None),
        ]
    )
    session.add_all(
        [
            models_alch.RoleRelationshipType(id=1, name='inverse'),
            models_alch.RoleRelationshipType(id=2, name='is_a'),
        ]
    )
    session.add_all(
        [
            models_alch.RoleRelationship(id=1, role1=1, role2=2, relationship_type=1),
            models_alch.RoleRelationship(id=16, role1=7, role2=1, relationship_type=2),
            models_alch.RoleRelationship(id=17, role1=8, role2=1, relationship_type=2),
        ]
    )
    session.flush()


def seed_references(session: Session) -> None:
    """
    Adds the record IDs referenced directly by tests.

    Called by: build_database()
    """
    references = [
        models_alch.Reference(id=4, citation_id=768, reference_type_id=13, national_context_id=1),
        models_alch.Reference(id=49, citation_id=768, reference_type_id=13, national_context_id=1),
        models_alch.Reference(id=895, citation_id=768, reference_type_id=13, national_context_id=1),
        models_alch.Reference(id=896, citation_id=768, reference_type_id=13, national_context_id=1),
        models_alch.Reference(id=1524, citation_id=768, reference_type_id=13, national_context_id=1),
    ]
    session.add_all(references)
    session.flush()


def seed_referents_and_relationships(session: Session) -> None:
    """
    Adds named referents and the relationships assumed by relationship tests.

    Called by: build_database()
    """
    add_referent(session, referent_id=4001, reference_id=4, first='No', last='Relationships')
    add_referent(session, referent_id=2033, reference_id=895, first='Test', last='Referent')
    add_referent(session, referent_id=2034, reference_id=896, first='First', last='Related')
    add_referent(session, referent_id=2037, reference_id=896, first='Second', last='Related')
    add_referent(session, referent_id=3703, reference_id=1524, first='Relationship', last='Subject')
    add_referent(session, referent_id=3704, reference_id=1524, first='Relationship', last='Object')
    session.flush()
    session.add_all(
        [
            models_alch.ReferentRelationship(id=2572, subject_id=2034, object_id=2037, role_id=1),
            models_alch.ReferentRelationship(id=16724, subject_id=3703, object_id=3704, role_id=7),
        ]
    )
    session.flush()


def add_referent(session: Session, referent_id: int, reference_id: int, first: str, last: str) -> None:
    """
    Adds a person, referent, and primary given name with stable IDs.

    Called by: seed_referents_and_relationships()
    """
    person = models_alch.Person(
        id=referent_id,
        first_name=first,
        last_name=last,
        comments='',
    )
    name = models_alch.ReferentName(
        id=referent_id,
        name_type_id=7,
        first=first,
        last=last,
    )
    referent = models_alch.Referent(
        id=referent_id,
        uuid=f'{referent_id:032d}',
        reference_id=reference_id,
        person=person,
        age='',
        sex='',
        occupation_text='',
    )
    referent.names.append(name)
    referent.primary_name = name
    session.add(referent)


def seed_audit_user(session: Session) -> None:
    """
    Adds the SQLAlchemy user matching Django's first temporary test user ID.

    Called by: build_database()
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    session.add(
        models_alch.User(
            id=1,
            role='tester',
            name='Django test user',
            email='test@example.org',
            created=now,
            last_login=now,
            password_hash='',
        )
    )
