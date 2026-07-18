"""
Manages sqlalchemy setup and queries.

Resources...
- <https://stackoverflow.com/questions/19406859/sqlalchemy-convert-select-query-result-to-a-list-of-dicts/20078977>
- <https://stackoverflow.com/questions/2828248/sqlalchemy-returns-tuple-not-dictionary>
- re type-annotations, the pattern ``foo = cast( mew-type, the-var )`` is used for two reasons:
  - that pattern does not actually cast, at run-time, "the-var" into the "new-type"; it's used for type-annotations.
  - this works with sqlalchemy since when evaluated at runtime, a Column( DateTime() ) will become a datetime.datetime() object.
"""

import datetime, logging, operator, pprint
from typing import cast  # just used for type-annotation

import sqlalchemy
from disa_app import settings_app
from sqlalchemy import Boolean, Float, Integer, String, ForeignKey, DateTime, UnicodeText
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session as alch_Session  # just used for type-annotation


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base


log = logging.getLogger(__name__)
Base = declarative_base()


## session configuration --------------------------------------------
"""
This implements a `singleton-pattern` for the SQLAlchemy engine and scoped_session, 
ensuring that these objects are instantiated only once.

The `scoped_session` exists only for the duration of a request, and is then removed.
"""

engine = None
ScopedSession = None

def initialize_engine_session():
    global engine, ScopedSession
    if engine is None:
        engine = create_engine( settings_app.DB_URL, echo=True )
        session_factory = sessionmaker( bind=engine )
        ScopedSession = scoped_session( session_factory )

def make_session():
    """
    Call this function to get a thread-local session
    for the current thread, initializing the engine and session factory
    if they haven't been initialized yet.
    """
    if engine is None or ScopedSession is None:
        initialize_engine_session()
    return ScopedSession

## Old session implementation. Problem here is that the engine-work happens each time, unnecessarily.
# def make_session() -> alch_Session:
#     engine = create_engine( settings_app.DB_URL, echo=True )
#     Session = sessionmaker( bind=engine )
#     session = Session()
#     return session

## Don't think this is needed, but leaving it here for now.
# def close_session(exception=None):
#     """
#     Call this function to close the thread-local session.
#     Optionally pass an exception if closing due to an exception.
#     """
#     if exception is not None:
#         # If there was an exception, you might want to rollback before closing
#         ScopedSession.rollback()
#     ScopedSession.remove()

## (end) session configuration --------------------------------------


# ==========
# RDF-ish
# ==========


# Base class for your models
Base = declarative_base()


citationtype_referencetypes = Table('3_citationtype_referencetypes',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('citation_type', Integer, ForeignKey('2_citation_types.id')),
    Column('reference_type', Integer, ForeignKey('1_reference_types.id')),
)


enslaved_as = Table('6_enslaved_as',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('referent', Integer, ForeignKey('5_referents.id')),
    Column('enslavement', Integer, ForeignKey('1_enslavement_types.id'))
)

has_origin = Table('6_has_origin',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('referent', Integer, ForeignKey('5_referents.id')),
    Column('origin', Integer, ForeignKey('1_locations.id'))
)


has_race = Table('6_has_race',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('referent', Integer, ForeignKey('5_referents.id')),
    Column('race', Integer, ForeignKey('1_races.id'))
)


has_role = Table('6_has_role',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('referent', Integer, ForeignKey('5_referents.id')),
    Column('role', Integer, ForeignKey('1_roles.id'))
)


has_title = Table('6_has_title',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('referent', Integer, ForeignKey('5_referents.id')),
    Column('title', Integer, ForeignKey('1_titles.id'))
)


has_tribe = Table('6_has_tribe',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('referent', Integer, ForeignKey('5_referents.id')),
    Column('tribe', Integer, ForeignKey('1_tribes.id'))
)


has_vocation = Table('6_has_vocation',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('referent', Integer, ForeignKey('5_referents.id')),
    Column('vocation', Integer, ForeignKey('1_vocations.id'))
)


referencetype_roles = Table('2_referencetype_roles',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('reference_type', Integer, ForeignKey('1_reference_types.id')),
    Column('role', Integer, ForeignKey('1_roles.id'))
)


# ==========
# models
# ==========



class Citation(Base):
    __tablename__ = '3_citations'

    id = Column(Integer, primary_key=True)

    # uuid = Column( String(32) )

    citation_type_id = Column(Integer, ForeignKey('2_citation_types.id'),
        nullable=False)
    display = Column(String(500))
    zotero_id = Column(String(255))
    comments = Column(UnicodeText())
    acknowledgements = Column(String(255))
    references = relationship('Reference', backref='citation', lazy=True)

    # def dictify( self ):  # branches dev & main, 2021-Apr-01
    #     jsn_references = []
    #     for rfrnc in self.references:
    #         jsn_references.append( rfrnc.dictify() )
    #     data = {
    #         'id': self.id,
    #         'citation_type_id': self.citation_type_id,
    #         'display': self.display,
    #         'zotero_id': self.zotero_id,
    #         'comments': self.comments,
    #         'references': jsn_references
    #         }
    #     return data

    def dictify( self ):  # branch new_flow, 2021-Apr-01
        jsn_references = []
        for rfrnc in self.references:
            jsn_references.append( rfrnc.dictify() )
        data = {
            'id': self.id,
            'citation_type_id': self.citation_type_id,
            'citation_type_name': self.citation_type.name,
            'display': self.display,
            'zotero_id': self.zotero_id,
            'comments': self.comments,
            'acknowledgements': self.acknowledgements,
            'references': jsn_references,
            'fields': { f.field.name: f.field_data for f in self.citation_data }  # note: `citation_data` is the "backref" from class CitationField() `citation` (whew!).
            }
        return data

    def __repr__(self):
        return '<Citation {0}>'.format(self.id)


class CitationType(Base):
    __tablename__ = '2_citation_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    zotero_type_id = Column(Integer, ForeignKey('1_zotero_types.id'),
        nullable=False)
    reference_types = relationship(
        'ReferenceType', secondary=citationtype_referencetypes,
        back_populates='citation_types')
    citations = relationship('Citation',
        backref='citation_type', lazy=True)


class ZoteroType(Base):
    __tablename__ = '1_zotero_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    creator_name = Column(String(255))
    citation_types = relationship('CitationType',
        backref='zotero_type', lazy=True)


class ZoteroField(Base):
    __tablename__ = '1_zotero_fields'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    display_name = Column(String(255))


class ZoteroTypeField(Base):
    __tablename__ = '2_zoterotype_fields'

    id = Column(Integer, primary_key=True)
    zotero_type_id = Column(Integer, ForeignKey('1_zotero_types.id'))
    zotero_field_id = Column(Integer, ForeignKey('1_zotero_fields.id'))
    rank = Column(Integer)
    zotero_type = relationship(ZoteroType,
        primaryjoin=(zotero_type_id == ZoteroType.id),
        backref='template_fields')
    zotero_field = relationship(ZoteroField,
        primaryjoin=(zotero_field_id == ZoteroField.id),
        backref='templates')


class CitationField(Base):
    __tablename__ = '4_citation_fields'

    id = Column(Integer, primary_key=True)
    citation_id = Column(Integer, ForeignKey('3_citations.id'))
    field_id = Column(Integer, ForeignKey('1_zotero_fields.id'))
    field_data = Column(String(255))
    citation = relationship(Citation,
        primaryjoin=(citation_id == Citation.id),
        backref='citation_data')
    field = relationship(ZoteroField,
        primaryjoin=(field_id == ZoteroField.id),
        backref='citations')


class Reference(Base):
    __tablename__ = '4_references'

    id = Column(Integer, primary_key=True)
    citation_id = Column(Integer, ForeignKey('3_citations.id'),
        nullable=False)
    reference_type_id = Column(Integer, ForeignKey('1_reference_types.id'),
        nullable=False)
    national_context_id = Column(Integer, ForeignKey('1_national_context.id'),
        nullable=False)
    date = Column(DateTime())
    transcription = Column(UnicodeText())
    image_url = Column( String(500) )
    researcher_notes = Column(UnicodeText())
    referents = relationship(
        'Referent', backref='reference', lazy=True, cascade="delete")
    groups = relationship(
        'Group', backref='reference', lazy=True, cascade="delete")

    def last_edit(self):
        """ Note: self.edits is possible because of ReferenceEdit() """
        edits: list[tuple] = sorted([ (e.timestamp, e) for e in self.edits ],
             key=operator.itemgetter(0), reverse=True)
        log.debug( f'edits, ```{edits}```' )
        if edits:
            return_edits = edits[0][1]
        else:
            return_edits = None
        log.debug( f'return_edits, ``{return_edits}``' )
        log.debug( f'type(return_edits), ``{type(return_edits)}``' )
        return return_edits

    def display_date(self):
        if self.date:
            return self.date.strftime('%Y %B %d')
        else:
            return ''

    def display_location_info( self ):
        # session = make_session()
        locations_lst = []
        rfrnc_locations = self.locations
        log.debug( f'rfrnc_locations, ```{rfrnc_locations}```' )
        for rfrnc_location in rfrnc_locations:
            location_name = rfrnc_location.location.name
            location_type = None
            try:
                location_type = rfrnc_location.location_type.name
            except:
                log.exception( f'problem parsing rfrnc_location, ```{rfrnc_location.__dict__}```; traceback follows; processing will continue' )
            loc_dct = { 'location_name': location_name, 'location_type': location_type }
            log.debug( f'loc_dct, ```{loc_dct}```' )
            locations_lst.append( loc_dct )
        return locations_lst

    def dictify( self ):
        if self.date:
            datetime_obj = cast( datetime.datetime, self.date )
            isodate = datetime.date.isoformat( datetime_obj )
        else:
            isodate = ''
        jsn_referents = []
        for rfrnt in self.referents:
            jsn_referents.append( {'id': rfrnt.id, 'age': rfrnt.age, 'sex': rfrnt.sex} )
        last_edit = self.last_edit()
        if last_edit:
            last_edit_str: str = last_edit.timestamp.strftime( '%Y-%m-%d' )
        else: 
            last_edit_str = ''
        data = {
            'id': self.id,
            'citation_id': self.citation_id,
            'reference_type_id': self.reference_type_id,
            'reference_type_name': self.reference_type.name,  # NB: this appears to be an sqlalchemy convention -- that if there is a ForeignKey, I can just go ahead and refernce the property name.
            'national_context_id': self.national_context_id,
            'date': isodate,
            'transcription': self.transcription,
            'researcher_notes': self.researcher_notes,
            'referents': jsn_referents,
            'last_edit': last_edit_str,
            'location_info': self.display_location_info(),
            'citation_fields': { str(f.field_id): f.field_data for f in self.citation_fields }
            }
        return data

    def __repr__(self):
        return '<Reference {0}>'.format(self.id)

    ## end class ReferenceType()


class ReferenceType(Base):
    __tablename__ = '1_reference_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    references = relationship('Reference',
        backref='reference_type', lazy=True)
    roles = relationship(
        'Role', secondary=referencetype_roles,
        back_populates='reference_types')
    citation_types = relationship(
        'CitationType', secondary=citationtype_referencetypes,
        back_populates='reference_types')

    def dictify( self ):
        data = {
            'id': self.id,
            'name': self.name
            }
        return data

class ReferenceCitationField(Base):
    __tablename__ = '4_citation_fields_reference'

    id = Column(Integer, primary_key=True)
    reference_id = Column(Integer, ForeignKey('4_references.id'))
    field_id = Column(Integer, ForeignKey('1_zotero_fields.id'))
    field_data = Column(String(255))
    reference = relationship(Reference,
        primaryjoin=(reference_id == Reference.id),
        backref='citation_fields')
    field = relationship(ZoteroField,
        primaryjoin=(field_id == ZoteroField.id),
        backref='references')

class Location(Base):
    __tablename__ = '1_locations'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    origin_for = relationship('Referent',
        secondary=has_origin, back_populates='origins')

    def __repr__(self):
        return '<Location {0}: {1}>'.format(self.id, self.name)


class ReferenceLocation(Base):
    __tablename__ = '5_has_location'

    id = Column(Integer, primary_key=True)
    reference_id = Column(Integer, ForeignKey('4_references.id'))
    location_id = Column(Integer, ForeignKey('1_locations.id'))
    location_type_id = Column(Integer, ForeignKey('1_location_types.id'))
    location_rank = Column(Integer)
    reference = relationship(Reference,
        primaryjoin=(reference_id == Reference.id),
        backref='locations')
    location = relationship(Location,
        primaryjoin=(location_id == Location.id),
        backref='references')


class LocationType(Base):
    __tablename__ = '1_location_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    locations = relationship( ReferenceLocation,
        backref='location_type', lazy=True )


class Person(Base):
    __tablename__ = '1_people'

    id = Column( Integer, primary_key=True )
    first_name = Column( String(255) )
    last_name = Column( String(255) )
    comments = Column( String(255) )
    references = relationship( 'Referent', backref='person', lazy=True )

    @classmethod
    def filter_on_description( cls, desc ):
        return cls.query.join(
            cls.references).join(Referent.roles).filter(Role.name==desc)

    def display_name( self ):
        display = "{0} {1}".format(
            self.first_name, self.last_name).strip()
        if display == "":
            return "Unknown"
        else:
            return display

    def display_attr( self, attr ):
        vals = { desc.name for ref in self.references
            for desc in getattr(ref, attr) }
        return ', '.join(list(vals))

    def dictify( self ):
        data = {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'comments': self.comments,
            }
        return data

    def __repr__(self):
        display_repr = f'<Person {self.id}: {self.display_name()}>'
        return display_repr

    ## end class Person


class NationalContext(Base):
    __tablename__ = '1_national_context'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    references = relationship('Reference', backref='national_context', lazy=True)


class NameType(Base):
    __tablename__ = '1_name_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))  # eg 'Enlgish', 'European', 'Indian', 'Given', etc


class ReferentName(Base):
    __tablename__ = '6_referent_names'

    id = Column(Integer, primary_key=True)
    referent_id = Column(Integer, ForeignKey('5_referents.id'))
    # name_type_id = Column(Integer, ForeignKey('1_name_types.id'))
    name_type_id: int = cast( int, Column(Integer, ForeignKey('1_name_types.id')) )
    first = Column(String(255))
    last = Column(String(255))
    name_type = relationship(
        'NameType',
        primaryjoin=(name_type_id == NameType.id) )

    def __repr__(self):
        return f'<Referent id, ``{self.referent_id}``; first, ``{self.first}``; last, ``{self.last}``>'


class AgeCategory(Base):
    __tablename__ = '1_age_categories'
    uuid = Column(String(36), primary_key=True)
    name = Column(String(50), nullable=False)


class Referent(Base):
    __tablename__ = '5_referents'

    id = Column(Integer, primary_key=True)
    uuid: str = cast( str, Column(String(32)) )
    age = Column(String(255))
    age_number = Column(Float)  # New column for age_number
    age_category = Column(String(36), ForeignKey('1_age_categories.uuid'))  # New column for age_category
    sex = Column(String(255))
    primary_name_id = Column(Integer,
        ForeignKey('6_referent_names.id'),
        nullable=True)
    reference_id = Column(Integer, ForeignKey('4_references.id'),
        nullable=False)
    person_id = Column(Integer, ForeignKey('1_people.id'),
        nullable=True)
    occupation_text = Column(String(500))
    age_category_relation = relationship('AgeCategory')  # New relationship for age_category
    names = relationship(
        'ReferentName',
        primaryjoin=(id == ReferentName.referent_id),
        backref='referent',
        cascade='delete')
    primary_name = relationship(
        'ReferentName',
        primaryjoin=(primary_name_id == ReferentName.id),
        post_update=True )
    roles = relationship(
        'Role',
        secondary=has_role,
        back_populates='referents' )
    tribes = relationship(
        'Tribe',
        secondary=has_tribe,
        back_populates='referents' )
    races = relationship(
        'Race',
        secondary=has_race,
        back_populates='referents')
    race_text = Column(String(500))
    titles = relationship('Title',
        secondary=has_title, back_populates='referents')
    vocations = relationship('Vocation',
        secondary=has_vocation, back_populates='referents')
    origins = relationship('Location',
        secondary=has_origin, back_populates='origin_for')
    enslavements = relationship('EnslavementType',
        secondary=enslaved_as, back_populates='referents')

    def __repr__(self):
        return '<Referent {0}: {1}>'.format(
            self.id, self.display_name() )

    def display_name(self):
        display = "{0} {1}".format(
            self.primary_name.first, self.primary_name.last).strip()
        if display == "":
            return "Unknown"
        else:
            return display

    def dictify(self):
        enslavements = []
        for enslavement in self.enslavements:  # the data-entry form says 'status'; the db stores these as enslavements.
            enslavements.append( {'enslavement_db_id': enslavement.id, 'enslavement_name': enslavement.name} )
        rfrnt_names = []
        for rfrnt_name in self.names:
            rfrnt_names.append( {
                'rfrnt_name_db_id': rfrnt_name.id,
                'rfrnt_name_first': rfrnt_name.first,
                'rfrnt_name_last': rfrnt_name.last,
                'rfrnt_name_nametype': {'name_type_id': rfrnt_name.name_type.id, 'name_type_name': rfrnt_name.name_type.name}
                } )
        origins = []
        for origin in self.origins:
            origins.append( {'origin_db_id': origin.id, 'origin_name': origin.name} )
        races = []
        for race in self.races:
            races.append( {'race_db_id': race.id, 'race_name': race.name} )
        roles = []
        for role in self.roles:
            roles.append( {'enslavement_db_id': role.id, 'enslavement_name': role.name} )
        tribes = []
        for tribe in self.tribes:
            tribes.append( {'tribe_db_id': tribe.id, 'tribe_name': tribe.name} )
        vocations = []
        for vocation in self.vocations:
            # vocations.append( {'vocation_db_id': tribe.id, 'vocation_name': tribe.name} )
            vocations.append( {'vocation_db_id': vocation.id, 'vocation_name': vocation.name} )
        data = {
            'referent_db_id': self.id,
            'referent_uuid': None,
            'person_db_id': self.person_id,
            'reference_db_id': self.reference_id,
            'age': self.age,
            'enslavements': enslavements,
            'names': rfrnt_names,
            'origins': origins,
            'races': races,
            'roles': roles,
            'tribes': tribes,
            'vocations': vocations
        }
        return data

    ## end class Referent


class Group(Base):
    __tablename__ = 'groups'

    uuid: str = cast( str, Column(String(32), primary_key=True) )
    count: int = cast( int, Column(Integer) )
    count_estimated: bool = cast( bool, Column(Boolean) )
    description: str = cast( str, Column(UnicodeText()) )
    date_created: datetime.datetime = cast( datetime.datetime, Column(DateTime()) )
    date_modified: datetime.datetime = cast( datetime.datetime, Column(DateTime()) )
    reference_id: int = cast( int, Column(Integer, ForeignKey('4_references.id'), nullable=False) )


# class Group(Base):
#     __tablename__ = 'groups'

#     uuid = Column( String(32), primary_key=True )
#     count = Column( Integer )
#     count_estimated = Column( Boolean )
#     description = Column( UnicodeText() )
#     date_created = Column( DateTime() )
#     date_modified = Column( DateTime() )
#     reference_id = Column( Integer, ForeignKey('4_references.id'), nullable=False )


class Title(Base):
    __tablename__ = '1_titles'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    referents = relationship('Referent',
        secondary=has_title, back_populates='titles')


class Race(Base):
    __tablename__ = '1_races'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    referents = relationship(
        'Referent',
        secondary=has_race,
        back_populates='races' )


class Vocation(Base):
    __tablename__ = '1_vocations'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    referents = relationship('Referent',
        secondary=has_vocation, back_populates='vocations')


class EnslavementType(Base):
    __tablename__ = '1_enslavement_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    referents = relationship(
        'Referent',
        secondary=enslaved_as,
        back_populates='enslavements' )


class Role(Base):
    __tablename__ = '1_roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    name_as_relationship = Column(String(255))
    referents = relationship(
        'Referent',
        secondary=has_role,
        back_populates='roles' )
    reference_types = relationship(
        'ReferenceType',
        secondary=referencetype_roles,
        back_populates='roles' )


class ReferentRelationship(Base):
    __tablename__ = '6_referent_relationships'

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey('5_referents.id'))
    object_id = Column(Integer, ForeignKey('5_referents.id'))
    role_id = Column(Integer, ForeignKey('1_roles.id'))
    sbj = relationship(Referent,
        primaryjoin=(subject_id == Referent.id),
        backref=backref('as_subject', cascade='delete'))
    obj = relationship(Referent,
        primaryjoin=(object_id == Referent.id),
        backref=backref('as_object', cascade='delete'))
    related_as = relationship(Role,
        primaryjoin=(role_id == Role.id),
        backref='describes')

    def entailed_relationships(self):
        session = make_session()
        implied = []
        # entailed = RoleRelationship.query.filter_by(role1=self.role_id).all()
        entailed = session.query( RoleRelationship ).filter_by(role1=self.role_id).all()

        for e in entailed:
            implied.append(e.entail_relationships(
                self.subject_id, self.object_id))
        return implied


class RoleRelationship(Base):
    __tablename__ = '2_role_relationships'

    id = Column(Integer, primary_key=True)
    role1 = Column(Integer, ForeignKey('1_roles.id'))
    role2 = Column(Integer, ForeignKey('1_roles.id'))
    relationship_type = Column(Integer,
        ForeignKey('1_role_relationship_types.id'))
    alternate_text = Column(String(255))

    def entail_role(self):
        pass

    def entail_relationships(self, sbjId, objId):
        if self.related_as.name == 'inverse':
            return ReferentRelationship(
                subject_id=objId, role_id=self.role2, object_id=sbjId)
        elif self.related_as.name == 'is_a':
            return ReferentRelationship(
                subject_id=sbjId, role_id=self.role2, object_id=objId)
        else:
            return


class RoleRelationshipType(Base):
    __tablename__ = '1_role_relationship_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    relationships = relationship(
        'RoleRelationship', backref='related_as', lazy=True)


class Tribe(Base):
    __tablename__ = '1_tribes'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    referents = relationship(
        'Referent',
        secondary=has_tribe,
        back_populates='tribes' )


class User(Base):
    __tablename__ = '1_users'

    id = Column(Integer, primary_key=True)
    role = Column(String(64))
    name = Column(String(64))
    email = Column(String(120))
    created = Column(DateTime())
    last_login = Column(DateTime())
    password_hash = Column(String(128))


class ReferenceEdit(Base):
    __tablename__ = '5_reference_edits'

    id = Column(Integer, primary_key=True)
    reference_id = Column(Integer, ForeignKey('4_references.id'))
    user_id = Column(Integer, ForeignKey('1_users.id'))
    timestamp = Column(DateTime())
    edited = relationship(Reference,
        primaryjoin=(reference_id == Reference.id),
        backref='edits')
    edited_by = relationship(User,
        primaryjoin=(user_id == User.id),
        backref='edits')

    def __repr__(self):
        return f'<ReferenceEdit {self.id}>'
