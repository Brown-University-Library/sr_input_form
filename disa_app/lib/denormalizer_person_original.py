# -*- coding: utf-8 -*-

"""
Creates the json file used by the browse-table javascript library.

Usage...
- called by cron script in practice.
- can be called manually by cd-ing to the repository directory and running:
  $ uv run ./disa_app/lib/denormalizer_person_original.py
"""

import collections, datetime, json, logging, os, pathlib, pprint, sys
import django, sqlalchemy

from django.urls import reverse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
log.info( '\n\ndenormalizer log ready' )


def json_for_browse():
    """ Produces json used by 'browse'.
        Called by ```if __name__ == "__main__":``` """
    log.debug( 'starting json_for_browse()' )
    start_time = datetime.datetime.now()

    session = make_session()
    filter_deleted = FilterDeleted()

    persons = session.query( models_alch.Person ).all()
    log.debug( f'persons count, ``{len(persons)}``' )

    filtered_out_deleted_persons = filter_deleted.manage_filtration( persons, session )
    log.debug( f'filtered_out_deleted_persons count, ``{len(filtered_out_deleted_persons)}``' )

    persons_subset = list(
        { p for p in filtered_out_deleted_persons for r in p.references if None not in r.roles }
        )
    log.debug( f'persons_subset count, ``{len(persons_subset)}``' )

    out = []

    counter = 0
    for p in persons_subset:

        log.debug( f'p.id, ``{p.id}``' )

        counter += 1
        data = {}
        data['id'] = p.id
        data['first_name'] = p.first_name
        data['last_name'] = p.last_name

        log.debug( f'last_name, ``{data["last_name"]}``' )

        if data['first_name'] == '' and data['last_name'] == '':
            data['first_name'] = 'unrecorded'
        data['documents'] = collections.defaultdict(list)
        data['description'] = {
            'tribe': '',
            'sex': '',
            'origin': '',
            'vocation': '',
            'age': '',
            'race': '',
            'title': ''
        }
        data['status'] = 'enslaved'
        data['owner'] = ''
        data['has_mother'] = ''
        data['has_father'] = ''
        data['spouse'] = ''
        data['transcription'] = ''
        first_date = datetime.datetime(year=2018,day=1,month=1)
        for ref in p.references:
            citation = ref.reference.citation.display
            new_date = ref.reference.date or first_date

            if type( new_date ) == datetime.date:
                new_date = datetime.datetime.combine( new_date, datetime.time() )  # creates a datetime obj with seconds at `0`

            if new_date < first_date:
                first_date = new_date

            existing_ref_data = data['documents'][citation]  # 2020-Oct-13 -- weird -- this _always_ appears to return an empty list
            log.debug( f'existing_ref_data, ``{pprint.pformat( existing_ref_data )}``' )

            new_ref_data = process_reference(ref)
            log.debug( f'new_ref_data, ``{pprint.pformat( new_ref_data )}``' )
            # data['roles_for_tabulator'] = new_ref_data['roles_tabulator']  # no, it needs to be in the document section, because a document can have more than one item
            # del new_ref_data['roles_tabulator']   # no need to display it twice
            log.debug( f'data id, ``{data["id"]}``' )
            # break

            data['documents'][citation] = merge_ref_data(
                existing_ref_data, new_ref_data)
            for d in data['documents'][citation]:
                if d.get('description'):
                    ex_desc = data['description']
                    new_desc = d['description']
                    ex_desc['tribe'] = new_desc['tribe'] \
                        if new_desc['tribe'] else ex_desc['tribe']
                    ex_desc['sex'] = new_desc['sex'] \
                        if new_desc['sex'] else ex_desc['sex']
                    ex_desc['origin'] = new_desc['origin'] \
                        if new_desc['origin'] else ex_desc['origin']
                    ex_desc['vocation'] = new_desc['vocation'] \
                        if new_desc['vocation'] else ex_desc['vocation']
                    ex_desc['age'] = new_desc['age'] \
                        if new_desc['age'] else ex_desc['age']
                    ex_desc['race'] = new_desc['race'] \
                        if new_desc['race'] else ex_desc['race']
            for ref in data['documents'][citation]:
                if 'enslaved' in ref['roles']:
                    if len(ref['roles']['enslaved']) > 0:
                        data['owner'] = ref['roles']['enslaved'][0]
                if 'has_mother' in ref['roles']:
                    if len(ref['roles']['has_mother']) > 0:
                        data['has_mother'] = ref['roles']['has_mother'][0]
                if 'has_father' in ref['roles']:
                    if len(ref['roles']['has_father']) > 0:
                        data['has_father'] = ref['roles']['has_father'][0]
                if 'spouse' in ref['roles']:
                    if len(ref['roles']['spouse']) > 0:
                        data['spouse'] = ref['roles']['spouse'][0]
            for ref in data['documents'][citation]:
                data['comments'] = ref['comments']
        data['date'] = {
            'year': first_date.year,
            'month': first_date.month,
            'day': first_date.day
        }
        out.append(data)

        if counter > 5000:  # for development
            break

    elapsed_time = str( datetime.datetime.now() - start_time )
    log.debug( 'elapsed time, ```%s```' % elapsed_time )

    return out

    ## end def json_for_browse()


# ==========
# helpers
# ==========


def make_session() -> sqlalchemy.orm.session.Session:
    engine = create_engine( settings_app.DB_URL, echo=False )
    Session = sessionmaker( bind=engine )
    session = Session()
    return session


def process_reference(entrant):
    """ Called by json_for_browse() """

    log.debug( f'\n\nentrant, ``{entrant}``' )
    start_time = datetime.datetime.now()

    rec = entrant.reference
    locs = [ (loc.location_rank, loc.location.name)
                for loc in rec.locations ]
    date = rec.date or datetime.datetime(year=1492,day=1,month=1)
    ref_data = {
        'roles': collections.defaultdict(list),
        'roles_tabulator': collections.defaultdict( list ),
        'date': {
            'year': date.year,
            'month': date.month,
            'day': date.day
        },
        'locations': [ l[1] for l in sorted(locs, reverse=True) ],
        'comments': rec.transcription
    }
    ref_data['description'] = {
        'tribe': merge_entrant_attributes(entrant.tribes),
        'sex': entrant.sex,
        'origin': merge_entrant_attributes(entrant.origins),
        'vocation': merge_entrant_attributes(entrant.vocations),
        'age': entrant.age,
        'race': merge_entrant_attributes(entrant.races)
    }
    for role in entrant.roles:
        log.debug( f'role, ``{role}``' )
        log.debug( f'role.__dict__, ``{role.__dict__}``' )
        # 1/0
        ref_data['roles'][role.name] = []
        ref_data['roles_tabulator'][role.name] = []

        # ref_data['roles_tabulator'][role.name] = {
        #     'name_as_relationship': role.name_as_relationship,
        #     'people': []
        #     }
        # log.debug( f'roles-tabulator-entry, ``{ref_data["roles_tabulator"][role.name]}``' )

    ers = entrant.as_subject
    for er in ers:
        obj = er.obj
        # There is a data anomaly, likely due to merge
        ## BJD - 2020-Feb-19, re above: ???
        if obj is None:
            continue

        role = er.related_as.name
        if role == 'child':

            # invs = models.ReferentRelationship.query.filter_by(
            #     subject_id=obj.id, object_id=entrant.id).all()

            invs = session.query( models_alch.ReferentRelationship ).filter_by( subject_id=obj.id, object_id=entrant.id ).all()

            inv = [ i for i in invs if i.related_as.name in {'mother', 'father'}]
            if len(inv) > 0:
                role = 'has_' + inv[0].related_as.name

        other = "{} {}".format(
            obj.primary_name.first, obj.primary_name.last).strip()

        # tabulator_other = "{} {} {}".format(
        #     obj.primary_name.first, obj.primary_name.last, obj.id ).strip()

        tabulator_other = {
            'primary_first_name': obj.primary_name.first.strip(),
            'primary_last_name': obj.primary_name.last.strip(),
            'link': f'%s%s' % ( reverse('edit_person_root_url'), obj.id )
        }

        if other == '':
            other = 'unrecorded'
        ref_data['roles'][role].append(other)

        ref_data['roles_tabulator'][role].append( tabulator_other )

        # log.debug( 'people, ``%s``' % ref_data["roles_tabulator"][role] )
        # try:
        #     ref_data['roles_tabulator'][role]['people'].append( tabulator_other )
        # except Exception as e:
        #     log.debug( f'WARNING -- before error, ref_data-roles_tabulator was, ``{ref_data["roles_tabulator"]}``' )
        #     # raise Exception( e )


    ref_data['roles'] = dict(ref_data['roles'])

    ref_data['roles_tabulator'] = dict( ref_data['roles_tabulator'] )

    if 'has_mother' in ref_data['roles'] or 'has_father' in ref_data['roles']:
        if 'child' in ref_data['roles'] and ref_data['roles']['child']==[]:
            del ref_data['roles']['child']
    if 'mother' in ref_data['roles'] or 'father' in ref_data['roles']:
        if 'parent' in ref_data['roles']:
            del ref_data['roles']['parent']

    elapsed_time = str( datetime.datetime.now() - start_time )

    return ref_data

    ## end def def process_reference()


def merge_entrant_attributes(attList):
    """ Called by: process_reference() """
    return ','.join([ att.name for att in attList ])


def merge_ref_data(existingDataList, newData):
    """ Called by json_for_browse() """
    new_list = []
    merged = False
    for ex in existingDataList:
        ref_lock = (ex['date'], ex['locations'])
        ref_key = (newData['date'], newData['locations'])
        if ref_lock == ref_key:
            merged = merge_ref_roles(ex,newData)
            new_list.append(merged)
        else:
            new_list.append(ex)
    if not merged:
        new_list.append(newData)
    return new_list


def merge_ref_roles(o,n):
    """ Called by: merge_ref_data() """
    for k in n['roles']:
        if k in o['roles']:
            o['roles'][k] = list(set(
                o['roles'][k] + n['roles'][k]))
    return o


class FilterDeleted():

    def __init__( self ):
        pass

    def manage_filtration( self, persons, session ):
        deleted_referent_ids = self.get_deleted_referent_ids()
        deleted_referent_objs = self.get_deleted_referent_objs( deleted_referent_ids, session )
        persons_to_ignore = self.get_persons_to_ignore( deleted_referent_objs, session )
        filtered_persons = self.apply_filter( persons, persons_to_ignore, session )
        return filtered_persons

    def apply_filter( self, persons, persons_to_ignore, session ):
        filtered_persons = []
        for person in persons:
            person_check = 'init'
            for person_to_ignore in persons_to_ignore:
                if person.id == person_to_ignore.id:
                    person_check = 'found'
                    break
            if person_check == 'init':
                filtered_persons.append( person )
            else:
                log.debug( f'filtering out person, ``{person}``' )
                person_check = 'init'
        return filtered_persons

    def get_persons_to_ignore( self, deleted_referent_objs, session ):
        persons = []
        for deleted_referent_obj in deleted_referent_objs:
            person_obj = session.query( models_alch.Person ).filter_by( id=deleted_referent_obj.person_id ).first()
            log.debug( f'for referent ``{deleted_referent_obj}``, person is, ``{person_obj}``' )
            persons.append( person_obj )
        log.debug( f'persons to ignore, ``{persons}``' )
        return persons

    def get_deleted_referent_objs( self, deleted_referent_ids, session ):
        objs = []
        for referent_id in deleted_referent_ids:
            referent_obj = session.query( models_alch.Referent ).filter_by( id=referent_id ).first()
            objs.append( referent_obj )
        log.debug( f'referent objs, ``{objs}``' )
        return objs

    def get_deleted_referent_ids( self ):
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

    ## end class FilterDeleted()


if __name__ == "__main__":
    output = json_for_browse()
    unformatted_output_path = settings_app.DENORMALIZED_JSON_PATH
    log.debug( f'unformatted_output_path, ``{unformatted_output_path}``' )  # logging not currently working
    formatted_output_path = f'%s/denormalized_formatted.json' % pathlib.Path( settings_app.DENORMALIZED_JSON_PATH ).parent  # arguably it'd make more sense to have the DENORMALIZED_JSON_PATH be to a directory, and then build each full-path with the unformatted and formatted json file name. But I didn't want to tweak the settings right now.
    log.debug( f'formatted_output_path, ``{formatted_output_path}``' )
    log.debug( f'type(output), ``{type(output)}``' )
    jsn = json.dumps( output )
    pretty_jsn = json.dumps( output, sort_keys=True, indent=2 )
    with open( unformatted_output_path, 'w' ) as f:
        f.write( jsn )
    with open( formatted_output_path, 'w' ) as f2:
        f2.write( pretty_jsn )
