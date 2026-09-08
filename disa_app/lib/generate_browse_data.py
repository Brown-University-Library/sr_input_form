"""
Creates the json file used by the browse-table javascript library.

Usage...
- called by cron script in practice.
- can be called manually from the repository directory:
  $ uv run ./disa_app/lib/generate_browse_data.py
"""

import collections, datetime, json, logging, os, pathlib, pprint, sys
import django, sqlalchemy

from django.urls import reverse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session as alch_session  # just for type-checking


## configure django paths
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
cwd = os.getcwd()  # assumes the cwd is the project directory
if cwd not in sys.path:
    sys.path.append( cwd )
django.setup()

## ok, now django-related imports will work
from disa_app import models_sqlalchemy as models_alch
from disa_app import settings_app
from disa_app.models import MarkedForDeletion


## set up file logger
LOG_PATH = os.environ['DISA_DJ__LOG_PATH']
LOG_LEVEL = os.environ['DISA_DJ__LOG_LEVEL']
level_dct = { 'DEBUG': logging.DEBUG, 'INFO': logging.INFO }
logging.basicConfig(
    filename=LOG_PATH, level=level_dct[LOG_LEVEL],
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s', datefmt='%d/%b/%Y %H:%M:%S' )
log = logging.getLogger(__name__)
log.info( '\n\ngenerate-browse-data log ready' )


def manage_generation():
    """ Produces json used by 'browse'.
        Called by ```if __name__ == "__main__":``` """
    log.debug( 'starting manage_generation()' )
    start_time = datetime.datetime.now()
    session = make_session()

    ## referents ======================

    referents_all = session.query( models_alch.Referent ).all()
    log.debug( f'referents_all count, ``{len(referents_all)}``' )

    filter_deleted = FilterDeleted()
    referents = filter_deleted.manage_filtration( referents_all, session )
    log.debug( f'referents after deletion-removal count, ``{len(referents)}``' )

    ( output_dct, initialized_referent_dct ) = initialize_output()

    output_dct['meta']['referents_count'] = len( referents )
    output_dct['meta']['excluded_referents_count'] = len( referents_all ) - len( referents)

    for referent in referents:
        populate_output( referent, output_dct, initialized_referent_dct )

    ## groups =========================

    groups = session.query( models_alch.Group ).order_by( 'reference_id', 'date_created' )

    group_lst = []
    reference_ids = []
    for grp in groups:
        assert type(grp.uuid) == str
        assert type(grp.count) == int
        assert type(grp.count_estimated) == bool
        assert type(grp.description) == str
        assert type(grp.date_created) == datetime.datetime
        assert type(grp.date_modified) == datetime.datetime
        assert type(grp.reference_id) == int
        grp_dct = {  # if I need to create another group dct elsewhere, consider adding a dictify() function to the model.
            'group_uuid': grp.uuid,
            'count': grp.count,
            'estimated': grp.count_estimated,
            'description': grp.description,
            'date_created': str(grp.date_created ),
            'date_modified': str( grp.date_modified ),
            'reference_db_id': grp.reference_id
        }
        group_lst.append( grp_dct )
        if grp.reference_id not in reference_ids:
            reference_ids.append( grp.reference_id )

    output_dct['meta']['groups__total_count'] = len( group_lst )
    output_dct['meta']['groups__reference_count'] = len( reference_ids )
    output_dct['groups'] = group_lst

    ## other =========================

    output_dct['meta']['date_produced'] = str( start_time )
    output_dct['meta']['elapsed_time'] = str( datetime.datetime.now() - start_time )

    ## return

    # log.debug( f'output_dct, ``{pprint.pformat(output_dct)}``' )
    return output_dct

    ## end manage_generation()


def make_session() -> alch_session:
    """ Sets up sqlalchemy session.
        Called by manage_generation() controller. """
    engine = create_engine( settings_app.DB_URL, echo=False )
    Session = sessionmaker( bind=engine )
    session = Session()
    return session


def initialize_output() -> tuple:
    """ Sets up structs for ouput.
        Listed here for visual clarity.
        Called by manage_generation() controller. """
    initialized_output_dct = {
        'meta': {
            'date_produced': None,
            'elapsed_time': None,
            'referents_count': None,
            'excluded_referents_count': None,
            'groups__total_count': None,
            'groups__reference_count': None
        },
        'referent_list': [
        ],
        'groups': [
        ]
    }
    initialized_referent_dct = {
        'referent_db_id': '',
        'referent_uuid': '',
        'name_first': '',
        'name_last': '',

        'tribes': '',
        'sex': '',
        'origins': '',
        'vocations': '',
        'age': '',
        'races': '',

        'roles': '',
        'titles': '',
        'statuses': '',

        'citation_data': {},
        'reference_data': {},
    }
    return ( initialized_output_dct, initialized_referent_dct )


def populate_output( referent, output_dct, initialized_referent_dct ):
    """ Populates referent, citation, and reference data.
        Called by manage_generation() controller. """
    # if len( output_dct['referent_list'] ) > 1000:
    #     return
    referent_dct = initialized_referent_dct.copy()
    referent_dct['referent_db_id'] = referent.id
    referent_dct['referent_uuid'] = referent.uuid
    ( first_name, last_name ) = get_name( referent )
    referent_dct['name_first'] = first_name
    referent_dct['name_last'] = last_name

    referent_dct['tribes'] = get_tribes( referent )
    referent_dct['sex'] = get_sex( referent )
    referent_dct['origins'] = get_origins( referent )
    referent_dct['vocations'] = get_vocations( referent )
    referent_dct['age'] = get_age( referent )
    referent_dct['races'] = get_races( referent )

    referent_dct['titles'] = get_titles( referent )
    referent_dct['statuses'] = get_statuses( referent )

    referent_dct['roles'] = get_roles( referent )
    referent_dct['relationships'] = get_relationships( referent )

    ( citation_data, reference_data ) = get_citation_and_reference_data( referent )
    referent_dct['citation_data'] = citation_data
    referent_dct['reference_data'] = reference_data

    output_dct['referent_list'].append( referent_dct )
    return


def get_roles( referent ):
    """ Creates list of role names.
        Examples: ["Enslaved", "Runaway"] Also see get_statuses() below; roles and statuses can seem to overlap.
        Called by populate_output() """
    roles = []
    for role in referent.roles:
        roles.append( role.name )
    return roles


def get_relationships( referent ):
    """ Creates list of relationship dicts.
        Called by populate_output() """
    relationships = []
    referent_relationships = referent.as_subject
    for relationship in referent_relationships:
        log.debug( f'relationship, ``{relationship}``' )
        other = relationship.obj
        if other == None:
            log.debug( 'other was `None`, so skipping' )
            continue
        relationship_data = {
            'description': relationship.related_as.name_as_relationship,
            'related_referent_info': {
                'related_referent_db_id': other.id,
                'related_referent_first_name': other.primary_name.first.strip(),
                'related_referent_last_name': other.primary_name.last.strip(),
            }
        }
        relationships.append( relationship_data )
    return relationships


def get_name( referent ) -> tuple:
    """ Creates name-tuple.
        Possible TODO- instead, or also, supply fielded first-name and last-name.
        Called by populate_output() """
    # log.debug( f'referent.names, ``{referent.names}``' )
    # for name in referent.names:
    #     log.debug( f'referent-name.name_type, ``{name.name_type}``')
    try:
        name = referent.names[0]
        name_tuple = ( name.first, name.last )
    except Exception as e:
        log.exception( 'problem getting name; processing continues, returned name-tuple will contain `Unknown` entries' )
        name_tuple = ( 'zUnknown', 'zUnknown' )
    log.debug( f'name_tuple, ``{name_tuple}``' )
    return name_tuple


# def get_name( referent ):
#     """ Creates name-tuple.
#         Possible TODO- instead, or also, supply fielded first-name and last-name.
#         Called by populate_output() """
#     log.debug( f'referent.names, ``{referent.names}``' )
#     for name in referent.names:
#         log.debug( f'referent-name.name_type, ``{name.name_type}``')
#     name = referent.names[0]
#     name_tuple = ( name.first, name.last )
#     log.debug( f'name_tuple, ``{name_tuple}``' )
#     return name_tuple


def get_tribes( referent ):
    """ Creates list of tribe names.
        Called by populate_output() """
    tribes = []
    for tribe in referent.tribes:
        tribes.append( tribe.name )
    return tribes


def get_sex( referent ):
    """ Creates gender entry, or sets default.
        TODO- set the default not-recorded string to a constant, and use that whenever it's needed.
        Called by populate_output() """
    sex = referent.sex
    if sex:
        if len( sex.strip() ) == 0:
            sex = '(not-recorded)'
    else:
        sex = '(not-recorded)'
    return sex


def get_origins( referent ):
    """ Creates list of origin names.
        Often a list of one; example entries: "Cape Cod" or "Carolina" or "Spanish America"
        Called by populate_output() """
    origins = []
    for origin in referent.origins:
        origins.append( origin.name )
    return origins


def get_vocations( referent ):
    """ Creates list of vocation names.
        Called by populate_output() """
    vocations = []
    for vocation in referent.vocations:
        vocations.append( vocation.name )
    return vocations


def get_age( referent ):
    """ Creates age string or sets default.
        Examples: "22" or "about 23"
        TODO- set the default not-recorded string to a constant, and use that whenever it's needed.
        Called by populate_output() """
    age = '(not-recorded)'
    if referent.age:
        age = referent.age
    return age


def get_races( referent ):
    races = []
    for race in referent.races:
        races.append( race.name )
    return races


def get_titles( referent ):
    titles = []
    for title in referent.titles:
        titles.append( title.name )
    return titles


def get_statuses( referent ):
    statuses = []
    for status in referent.enslavements:  # yes, the data-entry form says 'status'; the db stores these as enslavements.
        statuses.append( status.name )
    return statuses


def get_citation_and_reference_data( referent ):
    refrnc = referent.reference
    cite = refrnc.citation
    citation_data = {
        'citation_db_id': cite.id,
        'citation_uuid': '(not-recorded)',
        'citation_type': cite.citation_type.name,
        'display': cite.display,
        # 'zotero_id': cite.zotero_id,
        'comments': cite.comments,
    }
    if refrnc.date:
        isodate = datetime.date.isoformat( refrnc.date )
    else:
        isodate = ''
    reference_data = {
        'reference_db_id': refrnc.id,
        'reference_uuid': '(not-recorded)',
        'reference_type':refrnc.reference_type.name,
        'national_context': refrnc.national_context.name,
        'date_db': str( refrnc.date ),
        'date_display': refrnc.display_date(),
        'transcription': refrnc.transcription,
        'image_url': refrnc.image_url,
        'locations': refrnc.display_location_info()
    }
    # refrnc.dictify()
    # citation_data = referent.reference.citation.dictify()
    return ( citation_data, reference_data )


class FilterDeleted():

    def __init__( self ):
        self.deleted_referent_ids = None  # added this for output dct

    def manage_filtration( self, referents_all, session ):
        """ Filters out referents marked for deletion, and referents to ignore.
            Called by manage_generation() """
        deleted_referent_ids = self.get_deleted_referent_ids()
        self.deleted_referent_ids = deleted_referent_ids
        referents_to_ignore = self.get_deleted_referent_objs( deleted_referent_ids, session )
        # persons_to_ignore = self.get_persons_to_ignore( deleted_referent_objs, session )
        filtered_referents = self.apply_filter( referents_all, referents_to_ignore, session )
        log.debug( f'returning ``{len(filtered_referents)}`` filtered-referents' )
        return filtered_referents

    def get_deleted_referent_ids( self ):
        """ Gets the referent-ids from the django-db of marked-for-deletion docs. 
            Called by manage_filtration() """
        referent_ids = []
        marked_entries = MarkedForDeletion.objects.all()
        for entry in marked_entries:
            doc = json.loads( entry.doc_json_data )
            references = doc.get( 'references', None )
            if references:
                for reference in references:
                    referents = reference.get( 'referents', None )
                    if referents:
                        for referent in referents:
                            referent_ids.append( referent['id'] )
        sorted_referent_ids = sorted( referent_ids )
        log.debug( f'referent_ids, ``{sorted_referent_ids}``' )
        return sorted_referent_ids

    def get_deleted_referent_objs( self, deleted_referent_ids, session ):
        """ Creates deleted referent-objects from the deleted_referent_ids. 
            Called by manage_filtration() """
        objs = []
        for referent_id in deleted_referent_ids:
            referent_obj = session.query( models_alch.Referent ).filter_by( id=referent_id ).first()
            if referent_obj == None:  # because the actual referent in the db may actually have  been deleted
                log.debug( f'not creating obj for referent_id, ``{referent_id}``, because although it\'s in the marked-for-deletion doc-data, the actual db-entry has been deleted.' )
                pass
            else:
                objs.append( referent_obj )
        log.debug( f'referent objs, ``{objs}``' )
        return objs

    def apply_filter( self, referents_all, referents_to_ignore, session ):
        filtered_referents = []
        for referent in referents_all:
            referent_check = 'init'
            for referent_to_ignore in referents_to_ignore:
                if referent.id == referent_to_ignore.id:
                    referent_check = 'ignore'
                    break
            if referent_check == 'init':
                filtered_referents.append( referent )
            else:
                log.debug( f'filtering out referent, ``{referent}``' )
                referent_check = 'init'
        log.debug( f'filtered_referents, ``{pprint.pformat(filtered_referents)}``' )
        return filtered_referents

    ## end class FilterDeleted()


if __name__ == '__main__':
    output = manage_generation()
    unformatted_output_path = os.environ[ 'DISA_DJ__BROWSE_JSON_PATH' ]
    log.debug( f'unformatted_output_path, ``{unformatted_output_path}``' )
    formatted_output_path = f'%s/browse_formatted.json' % pathlib.Path( unformatted_output_path ).parent
    log.debug( f'formatted_output_path, ``{formatted_output_path}``' )
    log.debug( f'type(output), ``{type(output)}``' )
    jsn = json.dumps( output )
    pretty_jsn = json.dumps( output, sort_keys=True, indent=2 )
    with open( unformatted_output_path, 'w' ) as f:
        f.write( jsn )
    with open( formatted_output_path, 'w' ) as f2:
        f2.write( pretty_jsn )
