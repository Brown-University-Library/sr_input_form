# -*- coding: utf-8 -*-

"""
Creates the json file used by the browse-table javascript library.

Usage...
- called by cron script in practice.
- can be called manually by cd-ing to the project directory and running:
  $ uv run ./disa_app/lib/denormalizer_person_original.py
"""

import collections, datetime, json, logging, os, pathlib, pprint, sys
import django, sqlalchemy

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


log = logging.getLogger(__name__)


def make_session() -> sqlalchemy.orm.session.Session:
    engine = create_engine( settings_app.DB_URL, echo=True )
    Session = sessionmaker( bind=engine )
    session = Session()
    return session


def json_for_browse():
    """ Produces json used by 'browse'.
        Called manually for now. """
    log.debug( 'starting json_for_browse()' )
    start_time = datetime.datetime.now()

    session = make_session()

    # persons = models.Person.query.all()
    persons = session.query( models_alch.Person ).all()

    # owner_role = models.Role.query.filter_by(name='owner').first()
    owner_role = session.query( models_alch.Role ).filter_by( name='owner' ).first()

    ensl = list({ p for p in persons
        for r in p.references if owner_role not in r.roles })
    out = []
    for p in ensl:
        data = {}
        data['id'] = p.id
        data['first_name'] = p.first_name
        data['last_name'] = p.last_name
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
            existing_ref_data = data['documents'][citation]
            new_ref_data = process_reference(ref)
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

    elapsed_time = str( datetime.datetime.now() - start_time )
    log.debug( 'elapsed time, ```%s```' % elapsed_time )

    return out

    ## end def json_for_browse()


# ==========
# helpers
# ==========


def process_reference(entrant):
    """ Called by json_for_browse() """

    log.debug( 'starting process_reference()' )
    start_time = datetime.datetime.now()

    rec = entrant.reference
    locs = [ (loc.location_rank, loc.location.name)
                for loc in rec.locations ]
    date = rec.date or datetime.datetime(year=1492,day=1,month=1)
    ref_data = {
        'roles': collections.defaultdict(list),
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
        ref_data['roles'][role.name] = []
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
        if other == '':
            other = 'unrecorded'
        ref_data['roles'][role].append(other)
    ref_data['roles'] = dict(ref_data['roles'])
    if 'has_mother' in ref_data['roles'] or 'has_father' in ref_data['roles']:
        if 'child' in ref_data['roles'] and ref_data['roles']['child']==[]:
            del ref_data['roles']['child']
    if 'mother' in ref_data['roles'] or 'father' in ref_data['roles']:
        if 'parent' in ref_data['roles']:
            del ref_data['roles']['parent']

    elapsed_time = str( datetime.datetime.now() - start_time )
    log.debug( 'elapsed time, ```%s```' % elapsed_time )

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
