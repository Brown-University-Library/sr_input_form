# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint

import django, sqlalchemy
from disa_app import settings_app
from disa_app import models_sqlalchemy as models_alch
from disa_app.lib import person_common
from django.conf import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from disa_app.models import MarkedForDeletion


log = logging.getLogger(__name__)


def make_session() -> sqlalchemy.orm.session.Session:
    engine = create_engine( settings_app.DB_URL, echo=True )
    Session = sessionmaker( bind=engine )
    session = Session()
    return session


def query_documents( username: str, old_usr_db_id: int ) -> dict:
    """ Queries and massages data.
        Called by views.redesign_citations() """
    from sqlalchemy.orm import joinedload
    log.debug( 'starting query_documents()' )
    log.debug( f'username, ``{username}``; old_usr_db_id, ``{old_usr_db_id}``' )
    marked = MarkedForDeletion.objects.all()
    log.debug( f'marked, ``{marked}``' )
    log.debug( f'count of marked, ``{marked.count()}``' )
    marked_ids = []
    all_cites = []
    session = make_session()
    # cites_result_set = session.query( models_alch.Citation ).all() -- problemmatic
    # cites_result_set = session.query( models_alch.Citation ).options( joinedload(models_alch.Citation.references) ).all()  # solves first multiple-SELECTs
    cites_result_set = (session.query(models_alch.Citation)
                        .options(joinedload(models_alch.Citation.references)
                                .joinedload(models_alch.Reference.edits)
                                )
                        .all()
                        )
    if marked:
        for entry in marked:
            marked_ids.append( entry.old_db_id )
        for cite in cites_result_set:
            if cite.id not in marked_ids:
                all_cites.append( cite )
            else:
                log.debug( f'skipping cite, ``{cite}``' )
    else:
        all_cites = cites_result_set
    log.debug( 'marked_ids and all_cites lists populated' )  # ok, to this point, only one query which takes no time.

    data = {}
    log.debug( f'type(all_cites), ``{type(all_cites)}``')
    log.debug( 'about to build no_refs list' )
    no_refs = [ (cite, old_usr_db_id, datetime.datetime.now(), '')
        for cite in all_cites if len(cite.references) == 0 ]
    log.debug( 'no_refs list built; about to build has_refs list' )
    cites_with_refs: list = [ cite
        for cite in all_cites if len(cite.references) > 0 ]
    log.debug( 'has_refs list built; about to build wrapped_refs' )
    wrapped_refs: list = make_wrapped_refs( cites_with_refs )
    log.debug( 'wrapped_refs built; about to build user_cites list' )
    user_cites = [ wrapped
        for wrapped in wrapped_refs if wrapped[1] == old_usr_db_id ]
    log.debug( 'user_cites list built; about to build srtd_all' )
    srtd_all = sort_documents( wrapped_refs )
    log.debug( 'srtd_all built; about to build srtd_user' )
    srtd_user = sort_documents( user_cites )
    log.debug( 'srtd_user built; about to build user_documents' )
    data['user_documents'] = jsonify_entries( srtd_user[0:10] )
    log.debug( 'user_documents built; about to build documents' )
    data['documents'] = jsonify_entries( srtd_all )
    log.debug( f'data (first 1K chars), ```{pprint.pformat(data)[0:1000]}...```' )
    log.debug( 'returning data' )
    return data


def make_wrapped_refs( cites_with_refs: list ) -> list:
    """ Takes list of citation-objects,
        Returns list of tuples, with each tuple comprised of a citation-object, the (last?) editor-id, the (last?) editor-timestamp, and the (last?) editor-email.
        Example incoming data...
            [ <Citation 1>, <Citation 2>, <Citation 3>, ... ]
        Example returned data...
            [
                (<Citation 1>, 18, datetime.datetime(2018, 1, 23, 0, 54, 3), 'editor_a@brown.edu'),
                (<Citation 1>, 33, datetime.datetime(2020, 4, 27, 14, 38, 53), 'editor_b@brown.edu'),
                ...
            ]
        Making this into a function instead of a list comprehension for clarity.
        Called by query_documents() """
    wrapped_refs = []
    for cite in cites_with_refs:
        for ref in cite.references:
            for edit in ref.edits:
                try:
                    email = edit.edited_by.email
                except:
                    log.warning( 'email unavailable' )
                    email = 'not_available'
                wrapped_refs.append( (cite, edit.user_id, edit.timestamp, email) )
    log.debug( f'wrapped_refs (first 5) of `{len(wrapped_refs)}`, ```{pprint.pformat(wrapped_refs[0:5])}...```' )
    return wrapped_refs


def sort_documents( wrapped_refs: list ) -> list:
    """ Sorts citations by the date of most-recent-update.
        Example incoming data...
            [
                ( <Citation 1>, 18, datetime.datetime(2018, 1, 23, 0, 54, 3), 'editor_a@brown.edu' ),
                ( <Citation 1>, 33, datetime.datetime(2020, 4, 27, 14, 38, 53), 'editor_b@brown.edu' ),
                ...
            ]
        Example returned data...
            [
                ( datetime.datetime(2024, 7, 30, 19, 36, 23), 'editor_x@brown.edu', <Citation 2363> ),
                ( datetime.datetime(2024, 7, 30, 18, 48, 7), 'editor_y@brown.edu', <Citation 2381> )
            ]
        The "merge" work explanation...
            - The code iterates over each wrapped_refs-tuple. For each wrapped_refs tuple:
                - Checks if the citation's ID (w[0].id) is not already in the merge dictionary or if the current tuple's update time (w[2]) is more recent than the stored one.
                    - If either condition is true, updates the merge dictionary with the current tuple's update time, editor email, and citation object.
                    - Otherwise, skips to check the next tuple.
        Called by query_documents() """
    log.debug( f'before sort (first 5), ``{pprint.pformat(wrapped_refs[0:5])}``...' )
    merge = {}
    for (i, w) in enumerate(wrapped_refs):
        if w[0].id not in merge or merge[w[0].id][0] < w[2]:
            merge[w[0].id] = (w[2], w[3], w[0])
        else:
            continue
    log.debug( 'merge built' )
    try:
        sorted_docs = sorted( [merge[w] for w in merge], key=lambda x: x[0], reverse=True )  # sorts on date-time tuple-element (most-recent first)
    except Exception as e:
        log.exception( f'error on sort' )
        log.debug( f'w[0], ``{w[0]}``' )
        log.debug( f'w[0].__dict__, ``{pprint.pformat(w[0].__dict__)}``' )
        raise Exception( e )
    log.debug( f'after sort (first 5), ``{pprint.pformat(sorted_docs[0:5])}``...' )
    return sorted_docs


# def sort_documents( wrappedDocs ) -> list:
#     """ Sorts documents.
#         Called by query_documents() """
#     log.debug( f'before sort (first 5), ```{pprint.pformat(wrappedDocs[0:5])}```...' )
#     merge = {}
#     for w in wrappedDocs:
#         if w[0].id not in merge or merge[w[0].id][0] < w[2]:
#             merge[w[0].id] = (w[2], w[3], w[0])
#         else:
#             continue
#     sorted_docs = sorted([ merge[w] for w in merge], reverse=True)
#     log.debug( f'after sort (first 5), ```{pprint.pformat(sorted_docs[0:5])}```...' )
#     return sorted_docs


def jsonify_entries( doc_list ) -> list:
    """ Converts data elements into json-compatible data-structures.
        Called by query_documents() """
    jsonified_entries = []
    for entry in doc_list:
        ( date, email, citation_obj ) = ( entry[0], entry[1], entry[2] )
        dtstr_date = date.strftime( '%Y-%m-%d')
        dtstr_time = date.strftime( '%I:%M %p' )
        truncated_display = citation_obj.display if len(citation_obj.display) < 100 else f'{citation_obj.display[0:98]}…'
        entry_dct = {
            'date': {'dt_date': dtstr_date, 'dt_time': dtstr_time},
            'email': email,
            'doc': {'id': citation_obj.id, 'display': truncated_display, 'reference_count': len(citation_obj.references) }
            }
        jsonified_entries.append( entry_dct )
    log.debug( f'jsonified_entries (first 3), ```{pprint.pformat(jsonified_entries[0:3])}```' )
    return jsonified_entries


## for reference -- accessing edits (was in query_documents() above)

    # for ( i, cite ) in enumerate( has_refs):
    #     log.debug( f'cite, `{cite}`' )
    #     log.debug( f'display, ```{cite.display}```' )
    #     log.debug( f'cite.references, ```{cite.references}```' )
    #     for rfrnc in cite.references:
    #         log.debug( f'rfrnc.edits for rfrnc.id `{rfrnc.id}`, ```{rfrnc.edits}```' )
    #     if i > 4:
    #         break
    # 1/0
