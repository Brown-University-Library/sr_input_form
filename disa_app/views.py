# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint, time
# from typing import List

import requests

# -- sqlalchemy.orm.session.Session --
# import sqlalchemy
# from sqlalchemy import orm.session.Session
# from sqlalchemy.orm import session.Session
from sqlalchemy.orm.session import Session as AlchSession

# from disa_app.lib import basic_auth
# from django.shortcuts import get_object_or_404, render
from disa_app import settings_app
from disa_app.lib import denormalizer_document
from disa_app.lib import user_pass_auth
from disa_app.lib import utility_manager
from disa_app.lib import v_data_document_manager  # api/documents
from disa_app.lib import v_data_relationships_manager  # api/relationship-by-reference
from disa_app.lib import view_browse_manager
from disa_app.lib import view_data_entrant_manager  # api/referents
from disa_app.lib import view_data_group_manager  # api/groups
from disa_app.lib import view_data_records_manager  # api/items
from disa_app.lib import view_edit_record_manager
from disa_app.lib import view_edit_relationship_manager
from disa_app.lib import view_editor_index_manager, view_edit_citation_manager  # documents
from disa_app.lib import view_info_manager
from disa_app.lib import view_people_manager, view_person_manager, view_edit_referent_manager  # people
from disa_app.lib import view_search_results_manager
from disa_app.lib.shib_auth import shib_login  # decorator
from django.conf import settings as project_settings
from django.contrib.auth import logout as django_logout
from django.urls import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render

from disa_app import models_sqlalchemy


log = logging.getLogger(__name__)


# ===========================
# main urls
# ===========================


def info( request ):
    """ Displays temporary home page which will redirect to the public disa page.
        TODO: implement auto-redirect after a few seconds. """
    log.debug( '\n\nstarting info()' )
    context = {
        'redirect_url': 'https://indigenousslavery.org'
        }
    if request.GET.get('format', '') == 'json':
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        resp = render( request, 'info.html', context )
    return resp


def browse_tabulator( request ):
    """ Displays tabulator page. """
    log.info( '\n\nstarting browse_tabulator()' )
    log.debug( f'request.session.items(), ``{pprint.pformat(request.session.items())}``' )
    ( submitted_username, submitted_password ) = ( request.POST.get('browse_login_username', ''), request.POST.get('browse_login_password', '') )
    assert type(submitted_username) == str; assert type(submitted_password) == str
    resp = HttpResponseNotFound( '404 / Not Found' )
    if request.method == 'POST':  # user has submitted browse login credentials
        credentials_valid = view_browse_manager.check_credentials_on_post( submitted_username, submitted_password )
        assert type( credentials_valid ) == bool
        if credentials_valid:  # redirect to a GET to show the browse data
            request.session['browse_logged_in'] = 'yes'
            request.session.pop( 'errant_browse_login_username', None )  # <https://stackoverflow.com/questions/11277432/how-can-i-remove-a-key-from-a-python-dictionary/15206537#15206537>
            request.session.pop( 'errant_browse_login_password', None )
        else:  # store any entered data to the session and redirect to a GET to the login form again
            ( request.session['errant_browse_login_username'], request.session['errant_browse_login_password'] ) = ( submitted_username, submitted_password )
        request.session.modified = True
        resp = view_browse_manager.prepare_self_redirect_on_post()
    if request.method == 'GET':
        log.debug( 'handling GET' )
        is_browse_logged_in = view_browse_manager.check_browse_logged_in_on_get( dict(request.session), bool(request.user.is_authenticated) )
        assert type(is_browse_logged_in) == bool
        if is_browse_logged_in:  # show the browse data
            log.debug( 'logged-in path' )
            # request.session.pop( 'browse_logged_in', None )
            # request.session.modified = True
            context = view_browse_manager.prepare_logged_in_get_context( bool(request.user.is_authenticated) )
            resp = view_browse_manager.prepare_get_response( request, context, 'browse_tabulator.html' )
        else:  # show the login form
            log.debug( 'not logged-in path' )
            ( errant_submitted_username, errant_submitted_password ) = ( request.session.get('errant_browse_login_username', ''), request.session.get('errant_browse_login_password', '') )
            assert type( errant_submitted_username ) == str; assert type( errant_submitted_password ) == str
            request.session.pop( 'errant_browse_login_username', None )
            request.session.pop( 'errant_browse_login_password', None )
            request.session.modified = True
            context = view_browse_manager.prepare_non_logged_in_get_context( errant_submitted_username, errant_submitted_password )
            resp = view_browse_manager.prepare_get_response( request, context, 'browse_login.html' )
            log.debug( 'ok should render the browse-login template' )
    return resp


def browse_logout( request ):
    """ Logs user out of _browse_ view (only). """
    log.debug( '\n\nstarting browse_logout()' )
    log.debug( f'dict(request.session) start, ``{pprint.pformat(dict(request.session))}``' )
    request.session['browse_logged_in'] = 'no'
    log.debug( f'dict(request.session) end, ``{pprint.pformat(dict(request.session))}``' )
    redirect_url = reverse( 'browse_url' )
    log.debug( f'redirect_url, ```{redirect_url}```' )
    return HttpResponseRedirect( redirect_url )

def map ( request ):
    resp = render( request, 'map.html' )
    return resp

def timeline ( request ):
    resp = render( request, 'timeline.html' )
    return resp

def source( request, src_id ):
    log.debug( f'\n\nstarting source(), with src_id, `{src_id}`' )
    redirect_url = reverse( 'edit_record_w_recid_url', kwargs={'rec_id': src_id} )
    log.debug( f'redirect_url, ```{redirect_url}```' )
    return HttpResponseRedirect( redirect_url )


@shib_login
def editor_index( request ):
    ## TODO: rename this url from `/editor/` to `/citations/`?
    log.debug( '\n\nstarting editor_index()' )

    start_time = datetime.datetime.now()
    log.debug( f'start_time, ``{start_time}``' )
    target_time = start_time + datetime.timedelta(seconds=2)
    log.debug( f'target_time, ``{target_time}``' )
    while datetime.datetime.now() < target_time:  # 2023-Aug-03 -- what's this for?
        log.debug( f'now_time is, ``{datetime.datetime.now()}``' )
        time.sleep( 1 )
        log.debug( 'slept' )
    log.debug( 'proceeding' )

    user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
    context: dict = view_editor_index_manager.query_documents( request.user.username, user_id )
    if request.user.is_authenticated:
        context['user_is_authenticated'] = True
        context['user_first_name'] = request.user.first_name
    if request.GET.get('format', '') == 'json':
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        resp = render( request, 'document_index.html', context )
    return resp


def search_results( request ):
    log.debug( '\n\nstarting search_results()' )
    srch_txt = request.GET.get( 'query', None )
    log.debug( f'query, ```{srch_txt}```'  )
    if srch_txt is None:
        context = {}
    else:
        context: dict = view_search_results_manager.run_search( srch_txt[0:50], datetime.datetime.now() )
    if request.user.is_authenticated:
        context['user_is_authenticated'] = True
        context['user_first_name'] = request.user.first_name
    if request.GET.get('format', '') == 'json':
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        resp = render( request, 'search_results.html', context )
    return resp


@shib_login
def datafile( request ):
    """ Prepares complete denormalized datafile. """
    log.debug( '\n\nstarting datafile()' )
    srch_txt = request.GET.get( 'query', None )
    data: list = denormalizer_document.denormalize()
    j_string = json.dumps(data, sort_keys=True, indent=2)
    if request.GET.get('format', '') == 'json':
        resp = HttpResponse( j_string, content_type='application/json; charset=utf-8' )
    else:
        resp = render( request, 'denormalized_document.html', {'j_string': j_string, 'search_query': srch_txt} )
    return resp


# ===========================
# auth urls
# ===========================

def login( request ):
    """ Displays form offering shib & non-shib logins.
        Called by click on header login link. """
    log.debug( '\n\nstarting login()' )
    context = {
        'login_then_citations_url': '%s?next=%s' % ( reverse('shib_login_url'), reverse('redesign_citations_url') ),
        'user_pass_handler_url': reverse('user_pass_handler_url'),
        'flag_maintenance': settings_app.MAINTENANCE_MODE
    }
    log.debug( f'initial default context, ``{pprint.pformat(context)}``' )
    if request.GET.get('format', '') == 'json':
        log.debug( f'json-context, ``{pprint.pformat(context)}``' )
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        pre_entered_username = request.session.get( 'manual_login_username', None )
        if pre_entered_username:
            context['manual_login_username'] = request.session.get( 'manual_login_username', None )
        pre_entered_password = request.session.get( 'manual_login_password', None )
        if pre_entered_password:
            context['manual_login_password'] = request.session.get( 'manual_login_password', None )
        context['manual_login_error'] = request.session.get( 'manual_login_error', None )
        context['LOGIN_PROBLEM_EMAIL'] = settings_app.LOGIN_PROBLEM_EMAIL
        log.debug( f'non-json-context, ``{pprint.pformat(context)}``' )
        resp = render( request, 'login_form.html', context )
    return resp


@shib_login
def handle_shib_login( request ):
    """ Handles authNZ, & redirects to citation-list.
        Called by click on login, and clicking shib-login button. """
    log.debug( '\n\nstarting shib_login()' )
    next_url = request.GET.get( 'next', None )
    log.debug( f'next_url, ```{next_url}```' )
    if not next_url:
        log.debug( f'session_keys, ```{list( request.session.keys() )}```' )
        if request.session.get( 'redirect_url', None ):
            redirect_url = request.session['redirect_url']
        else:
            # redirect_url = reverse( 'editor_index_url' )
            redirect_url = reverse( 'redesign_citations_url' )
    else:
        redirect_url = request.GET['next']  # may be same page
    if request.session.get( 'redirect_url', None ):  # cleanup
        request.session.pop( 'redirect_url', None )
    log.debug( 'redirect_url, ```%s```' % redirect_url )
    return HttpResponseRedirect( redirect_url )


def logout( request ):
    """ Logs _app_ out; shib logout not yet implemented.
        Called by click on Welcome/Logout link in header-bar. """
    redirect_url = request.GET.get( 'next', None )
    if not redirect_url:
        redirect_url = reverse( 'info_url' )
    django_logout( request )
    log.debug( 'redirect_url, ```%s```' % redirect_url )
    return HttpResponseRedirect( redirect_url )


def user_pass_handler( request ):
    """ Handles user/pass login.
        On auth success, redirects user to citations-list
        On auth failure, redirects back to views.login() """
    log.debug( 'starting user_pass_handler()' )
    # context = {}
    # return HttpResponse( 'user-pass-auth handling coming' )
    if user_pass_auth.run_authentication(request) is not True:  # puts param values in session
        resp =  user_pass_auth.prep_login_redirect( request )
    else:
        resp = user_pass_auth.prep_citations_redirect( request )
    return resp


# ===========================
# editor urls
# ===========================

## TODO: 2023-Feb-16 -- many if not all editor url functions may be able to be deleted

# @shib_login  # no longer needed; will delete
# def edit_citation( request, cite_id=None ):
#     """ Url: 'editor/documents/<cite_id>/' -- 'edit_citation_url' """
#     log.debug( '\n\nstarting edit_citation()' )
#     if cite_id:
#         log.debug( f'will hit citation-manager with cite_id, ```{cite_id}```' )
#         context: dict = view_edit_citation_manager.query_data( cite_id )
#         if context == None:
#             return HttpResponseNotFound( '404 / Not Found' )
#     else:
#         log.debug( 'will hit citation-manager with no cite_id' )
#         user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
#         context: dict = view_edit_citation_manager.manage_create( user_id )
#     if request.user.is_authenticated:
#         context['user_is_authenticated'] = True
#         context['user_first_name'] = request.user.first_name
#         context['can_delete_doc'] = request.user.profile.can_delete_doc
#     if request.GET.get('format', '') == 'json':
#         resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
#     else:
#         resp = render( request, 'document_edit.html', context )
#     return resp


@shib_login
def edit_person( request, rfrnt_id=None ):
    """ Url: '/editor/person/<rfrnt_id>/' -- 'edit_person_url' """
    log.debug( '\n\nstarting edit_person()' )
    context: dict = view_edit_referent_manager.prep_context( rfrnt_id, request.user.first_name, bool(request.user.is_authenticated) )
    if request.GET.get('format', '') == 'json':
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        resp = render( request, 'entrant_edit.html', context )
    return resp


@shib_login
def edit_record( request, rec_id=None ):
    """ Url: '/editor/records/<rec_id>/' -- 'edit_record_url' """
    log.debug( f'\n\nstarting edit_record(), with rec_id, `{rec_id}`' )
    if rec_id:
        log.debug( 'handling rec_id exists' )
        context: dict = view_edit_record_manager.prep_rec_id_context( rec_id, request.user.first_name, bool(request.user.is_authenticated) )
    else:
        log.debug( 'handling no rec_id' )
        context: dict = view_edit_record_manager.prep_doc_id_context( request.GET.get('doc_id', None), request.user.first_name, bool(request.user.is_authenticated) )
    log.debug( f'context, ``{context}``' )
    if request.GET.get('format', '') == 'json':
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        resp = render( request, 'record_edit.html', context )
    return resp


@shib_login
def edit_record_w_recid( request, rec_id=None ):
    """ Url: '/editor/records/<rec_id>/' -- 'edit_record_w_recid_url' """
    log.debug( f'\n\nstarting edit_record_w_recid(), with rec_id, `{rec_id}`' )
    context: dict = view_edit_record_manager.prep_rec_id_context( rec_id, request.user.first_name, bool(request.user.is_authenticated) )
    log.debug( f'context, ``{context}``' )
    if request.GET.get('format', '') == 'json':
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        resp = render( request, 'record_edit.html', context )
    return resp


@shib_login
def edit_relationships( request, rec_id: str ):
    """ Note: though this is in the 'editor' section here, the url doesn't contain `editor` -- possible TODO.
        Url: '/record/relationships/<rec_id>/' -- 'edit_relationships_url' """
    log.debug( f'\n\nstarting edit_relationships(), with rec_id, `{rec_id}`' )
    # log.debug( f'\nrequest.__dict__, ```{pprint.pformat(request.__dict__)}```' )
    context: dict = view_edit_relationship_manager.prep_context(
        rec_id, request.META['SCRIPT_NAME'],request.user.first_name, bool(request.user.is_authenticated) )
    if request.GET.get('format', '') == 'json':
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        resp = render( request, 'record_relationships.html', context )
    return resp


# ===========================
# data urls
# ===========================


@shib_login
def data_reference_group( request, incoming_uuid=None ):
    """ Called via ajax from views.edit_record() page
        Url: '/data/reference_group/<incoming_uuid>/' -- 'data_group_url' """
    log.debug( '\n\nstarting data_reference_group()' )
    # log.debug( f'request.body, ``{request.body}``' )
    # log.debug( f'request.POST, ``{pprint.pformat(request.POST)}``' )
    # log.debug( f'request.__dict__, ``{pprint.pformat(request.__dict__)}``' )
    start_time = datetime.datetime.now()
    request_url = '%s://%s%s' % (
        request.scheme, request.META.get('HTTP_HOST', '127.0.0.1'), request.META.get('REQUEST_URI', request.META['PATH_INFO']) )  # some info not available from client-test
    assert type(incoming_uuid) == str
    log.debug( f'incoming_uuid, ```{incoming_uuid}```' )
    log.debug( f'request.method, ```{request.method}```' )
    ## GET --------------------------------------
    if request.method == 'GET':
        data_group_getter = view_data_group_manager.Getter( request_url, start_time )
        params_valid = data_group_getter.validate_get_params( incoming_uuid )
        if params_valid:
            if data_group_getter.prelim_status_code == 200:
                resp = data_group_getter.manage_get()  # grp already in Getter() self.grp
            else:
                resp = HttpResponseNotFound( '404 / Not Found' )
        else:
            resp = HttpResponseBadRequest( '400 / Bad Request' )
    ## PUT --------------------------------------
    elif request.method == 'PUT':
        # log.debug( f'request.__dict__, ``{pprint.pformat(request.__dict__)}``' )
        data_group_updater = view_data_group_manager.Updater( request_url, start_time )
        params_valid = data_group_updater.validate_put_params( request.body )
        if params_valid:
            user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
            assert type(user_id) == int
            resp = data_group_updater.manage_put( incoming_uuid, user_id )
        else:
            resp = HttpResponseBadRequest( '400 / Bad Request' )
    ## POST --------------------------------------
    elif request.method == 'POST':
        data_group_poster = view_data_group_manager.Poster( request_url, start_time )
        # params_valid = data_group_poster.validate_post_params( dict(request.POST) )
        params_valid = data_group_poster.validate_post_params( request.body )
        if params_valid:
            user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
            assert type(user_id) == int
            # resp = data_group_poster.manage_post( dict(request.POST), user_id )
            resp = data_group_poster.manage_post( user_id )
        else:
            resp = HttpResponseBadRequest( '400 / Bad Request' )
    ## DELETE --------------------------------------
    elif request.method == 'DELETE':
        log.debug( 'DELETE detected' )
        data_group_deleter = view_data_group_manager.Deleter( request_url, start_time )
        params_valid = data_group_deleter.validate_delete_params( incoming_uuid )
        if params_valid:
            if data_group_deleter.prelim_status_code == 200:
                user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
                assert type(user_id) == int
                resp = data_group_deleter.manage_delete( user_id )  # grp-obj already stored as attribute
            else:
                log.debug( 'returning `404 / Not Found`' )
                resp = HttpResponseNotFound( '404 / Not Found' )
        else:
            resp = HttpResponseBadRequest( '400 / Bad Request' )
    else:
        log.warning( f'request.method, ``{request.method}`` detected; returning `400 / Bad Request`' )
        resp = HttpResponseBadRequest( '400 / Bad Request' )
    return resp

    ## end def data_reference_group()


@shib_login
def data_entrants( request, rfrnt_id: str ):
    """ Called via ajax by views.edit_record()
        Url: '/data/entrants/<rfrnt_id>/' -- 'data_referent_url' """
    log.debug( '\n\nstarting data_entrants()' )
    log.debug( f'rfrnt_id, ```{rfrnt_id}```' )
    log.debug( f'request.method, ```{request.method}```' )
    user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
    if request.method == 'GET':
        data_entrant_getter = view_data_entrant_manager.Getter()
        resp = data_entrant_getter.manage_get( rfrnt_id )
    elif request.method == 'PUT':
        data_entrant_updater = view_data_entrant_manager.Updater()
        resp = data_entrant_updater.manage_put( request.body, user_id, rfrnt_id )
    elif request.method == 'POST':
        data_entrant_poster = view_data_entrant_manager.Poster()
        resp = data_entrant_poster.manage_post( request.body, user_id, rfrnt_id )
    elif request.method == 'DELETE':
        log.debug( 'DELETE detected' )
        data_entrant_deleter = view_data_entrant_manager.Deleter()
        resp = data_entrant_deleter.manage_delete( user_id, rfrnt_id )
    else:
        msg = 'data_entrants() other request.method handling coming'
        log.warning( f'message returned, ```{msg}``` -- but we shouldn\'t get here' )
        resp = HttpResponse( msg )
    return resp


# @shib_login
# def data_entrants_details( request, rfrnt_id ):
#     """ Called via ajax by views.edit_person()
#         Updates referent details.
#         Url: 'data/entrants/details/<rfrnt_id>' -- 'data_entrants_details_url' """
#     log.debug( f'\n\nstarting data_entrants_details(), with rfrnt_id, ``{rfrnt_id}``, and method, ``{request.method}``' )
#     log.debug( f'payload, ```{pprint.pformat(request.body)}```' )
#     log.debug( f'request.user.profile.old_db_id, ``{request.user.profile.old_db_id}``' )
#     log.debug( f'request.user.id, ``{request.user.id}``' )
#     user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
#     log.debug( f'user_id, ``{user_id}``' )
#     data_entrant_details_updater = view_data_entrant_manager.Details_Updater()
#     context: dict = data_entrant_details_updater.manage_details_put( request.body, user_id, rfrnt_id )
#     resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
#     return resp


@shib_login
def data_entrants_details( request, rfrnt_id ):
    """ Called via ajax by views.edit_person()
        Updates referent details.
        Url: 'data/entrants/details/<rfrnt_id>' -- 'data_entrants_details_url' """
    log.debug( f'\n\nstarting data_entrants_details(), with rfrnt_id, ``{rfrnt_id}``, and method, ``{request.method}``' )
    log.debug( f'payload, ```{pprint.pformat(request.body)}```' )
    log.debug( f'request.user.profile.old_db_id, ``{request.user.profile.old_db_id}``' )
    log.debug( f'request.user.id, ``{request.user.id}``' )
    user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
    log.debug( f'user_id, ``{user_id}``' )
    data_entrant_details_updater = view_data_entrant_manager.Details_Updater()
    context: dict = data_entrant_details_updater.manage_details_put( request.body, user_id, rfrnt_id )
    resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    return resp


@shib_login
def data_records( request, rec_id=None ):
    """ Called via ajax by views.edit_record()
        Url: '/data/records/<rec_id>/' -- 'data_record_url' """
    log.debug( '\n\nstarting data_records' )
    # log.debug( f'request.__dict__, ``{pprint.pformat(request.__dict__)}``' )
    ## get db-session for this request ------------------------------
    db_session: AlchSession = models_sqlalchemy.make_session()
    
    context = {}
    try:
        log.debug( f'query_string, ``{request.META.get("QUERY_STRING", None)}``; rec_id, ``{rec_id}``; method, ``{request.method}``; payload, ``{request.body}``' )
        assert ( rec_id == None or type(rec_id) == str )
        user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
        log.debug( f'request.user.profile.old_db_id, ``{request.user.profile.old_db_id}``' )
        log.debug( f'request.user.id, ``{request.user.id}``' )
        assert type(user_id) == int, type(user_id)
        log.debug( f'user_id, ``{user_id}``' )
        log.debug( f'request.body, ``{request.body}``' )
        if request.method == 'GET':
            if rec_id:
                log.debug( 'here, because rec_id exists' )
                context: dict = view_data_records_manager.query_record( rec_id, db_session )
            else:
                log.debug( f'here, because rec_id is None' )
                context = { 'rec': {}, 'entrants': [] }
        elif request.method == 'PUT':
            context: dict = view_data_records_manager.manage_reference_put( rec_id, request.body, user_id, db_session )
        elif request.method == 'POST':
            # time.sleep( 10 )  # temp -- this was to mimic a db-hang to address a javascript issue
            context: dict = view_data_records_manager.manage_post( request.body, user_id, db_session )
        else:
            log.warning( 'shouldn\'t get here' )
    except:
        log.exception( 'problem handling request' )
    resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    db_session.close()
    return resp


@shib_login
def data_reference( request, rfrnc_id ):
    """ Called via ajax by views.edit_citation() on DELETE
        Handles api call when red `x` button is clicked in, eg, <http://127.0.0.1:8000/editor/documents/(123)/>
        Url: '/data/reference/<rfrnc_id>/' -- 'data_reference_url'
        TODO: Why isn't this part of the above data_records() function??!!
        """
    log.debug( f'\n\nstarting data_reference()' )
    log.debug( f'query_string, ``{request.META.get("QUERY_STRING", None)}``; rfrnc_id, ``{rfrnc_id}``; method, ``{request.method}``; payload, ``{request.body}``' )
    
    ## get db-session for this request ------------------------------
    db_session: AlchSession = models_sqlalchemy.make_session()
    
    assert type(rfrnc_id) == str
    context: dict = view_data_records_manager.manage_reference_delete( rfrnc_id, db_session )
    rspns = HttpResponseNotFound( '404 / Not Found' )
    if 'err' in context.keys():
        if context['err'] == '400 / Bad Request':
            rspns = HttpResponseBadRequest( '400 / Bad Request' )
        elif context['err'] == '404 / Not Found':
            rspns = HttpResponseNotFound( '404 / Not Found' )
    else:
        rspns = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    db_session.close()
    return rspns


# @shib_login
# def data_reference( request, rfrnc_id ):
#     """ Called via ajax by views.edit_citation() on DELETE
#         Handles api call when red `x` button is clicked in, eg, <http://127.0.0.1:8000/editor/documents/(123)/>
#         Url: '/data/reference/<rfrnc_id>/' -- 'data_reference_url'
#         TODO: Why isn't this part of the above data_records() function??!!
#         """
#     log.debug( f'\n\nstarting data_reference()' )
#     log.debug( f'query_string, ``{request.META.get("QUERY_STRING", None)}``; rfrnc_id, ``{rfrnc_id}``; method, ``{request.method}``; payload, ``{request.body}``' )
#     assert type(rfrnc_id) == str
#     context: dict = view_data_records_manager.manage_reference_delete( rfrnc_id )
#     rspns = None
#     if 'err' in context.keys():
#         if context['err'] == '400 / Bad Request':
#             rspns = HttpResponseBadRequest( '400 / Bad Request' )
#         elif context['err'] == '404 / Not Found':
#             rspns = HttpResponseNotFound( '404 / Not Found' )
#     else:
#         rspns = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
#     return rspns


@shib_login
def data_documents( request, doc_id=None ):
    """ Called via ajax by views.edit_citation()
        Url: '/data/documents/<docId>/' -- 'data_documents_url' """
    log.debug( f'\n\nstarting data_documents, with doc_id, `{doc_id}`; with method, ```{request.method}```, with a payload of, `{request.body}`' )
    log.debug( f'request.user.id, ```{request.user.id}```; request.user.profile.old_db_id, ```{request.user.profile.old_db_id}```,' )
    log.debug( f'type(request.user.id), ```{type(request.user.id)}```; type(request.user.profile.old_db_id), ```{type(request.user.profile.old_db_id)}```,' )

    ## get db-session for this request ------------------------------
    db_session: AlchSession = models_sqlalchemy.make_session()
    log.debug( f'type(db_session), ``{type(db_session)}``' )

    ## get user info ------------------------------------------------
    user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
    user_uuid = request.user.profile.uu_id
    user_email = request.user.profile.email
    log.debug( f'user_id, ```{user_id}```' )
    context = {}
    if request.method == 'GET' and doc_id:
        context: dict = v_data_document_manager.manage_get( doc_id, user_id, db_session )
    elif request.method == 'GET':  # called when clicking 'New document' button
        context: dict = v_data_document_manager.manage_get_all( user_id, db_session )
    elif request.method == 'PUT':
        context: dict = v_data_document_manager.manage_put( doc_id, user_id, request.body, db_session )
    elif request.method == 'POST':
        context: dict = v_data_document_manager.manage_post( user_id, request.body, db_session )
    elif request.method == 'DELETE':
        log.debug( 'DELETE detected' )
        context: dict = v_data_document_manager.manage_delete( doc_id, user_uuid.hex, user_email, db_session )
    else:
        msg = 'data_documents() other request.method handling coming'
        log.warning( f'message returned, ```{msg}``` -- but we shouldn\'t get here' )
        resp = HttpResponse( msg )
    log.debug( f'context, ``{context}``' )
    if context == 'error':  # TODO: merge this response into `400 / Bad Request`
        resp = HttpResponseBadRequest( '400 / Bad Request' )
    # elif context == '400 / Bad Request':
    #     resp = HttpResponseBadRequest( '400 / Bad Request' )
    elif type(context) == dict and 'err' in context.keys() and context['err'] == '400 / Bad Request':
        resp = HttpResponseBadRequest( '400 / Bad Request' )
    elif context == 'not_found':
        resp = HttpResponseNotFound( '404 / Not Found' )
    elif context == '500 / Server Error':
        resp = HttpResponseServerError( context )
    else:
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    db_session.close()
    return resp


def data_root( request ):
    """ Not called directly; this is a convenience feature for building other urls in javascript
        Url: '/data/' -- 'data_root_url' """
    return HttpResponseNotFound( '404 / Not Found' )


@shib_login
def relationships_by_reference( request, rfrnc_id ):
    """ Called via ajax by views.edit_relationships() when page is loaded.
        Url: '/data/sections/<rfrnc_id>/relationships/' -- 'data_reference_relationships_url' """
    log.debug( '\n\nstarting relationships_by_reference()' )
    log.debug( f'query_string, ``{request.META.get("QUERY_STRING", None)}``; rfrnc_id, ``{rfrnc_id}``; method, ``{request.method}``; payload, ``{request.body}``' )
    context: dict = v_data_relationships_manager.prepare_relationships_by_reference_data( rfrnc_id )
    resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    return resp

@shib_login
def data_relationships( request, rltnshp_id=None, record_id=None ):
    """ Called via ajax by views.edit_relationships() when `+` buton is clicked.
        Url: '/data/relationships/' -- 'data_relationships_url' 
        NOTE: 
        - the response will be a redirect to the record (the "reference").
        - the response.content will contain a json-string showing, eg, `{"relationship_id": 123, "new_relationship": true}`.
        - the reason for the new_relationship boolean is to distinguish, in testing, whether the relationship was created or already-existing.
        - as of 2023-June, the response.content is not being used by the front-end javascript.
        """
    log.debug( '\n\nstarting data_relationships()' )
    log.debug( f'query_string, ``{request.META.get("QUERY_STRING", None)}``; rltnshp_id, ``{rltnshp_id}``; method, ``{request.method}``; payload, ``{request.body}``' )
    user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
    if request.method == 'POST':
        log.debug( 'starting POST flow handling' )
        relationship_dict: dict = v_data_relationships_manager.manage_relationships_post( request.body, user_id )
        rfrnc_id = relationship_dict['rfrnc_id']; assert type(rfrnc_id) == int
        relationship_id = relationship_dict['relationship_id']; assert type(relationship_id) == int
        relationship_is_new = relationship_dict['relationship_is_new']; assert type(relationship_is_new) == bool
        redirect_url = reverse( 'data_reference_relationships_url', kwargs={'rfrnc_id': rfrnc_id} )
        log.debug( f'redirect_url, ```{redirect_url}```' )
        # resp = HttpResponseRedirect( redirect_url )
        # resp = HttpResponseRedirect( redirect_url, 'FOO2' )
        content_json = json.dumps( relationship_dict )
        resp = HttpResponseRedirect( redirect_to=redirect_url, content=content_json )
    elif request.method == 'DELETE':
        log.debug( 'starting DELETE flow handling' )
        record_id = str( record_id )
        assert type(record_id) == str
        # reference_id = record_id
        log.debug( f'record_id, ``{record_id}``')
        rfrnc_id: str = v_data_relationships_manager.manage_relationships_delete( rltnshp_id, record_id, user_id )  # type: ignore
        redirect_url = reverse( 'data_reference_relationships_url', kwargs={'rfrnc_id': rfrnc_id} )
        log.debug( f'redirect_url, ``{redirect_url}```' )
        resp = HttpResponseRedirect( redirect_url )
    else:
        log.warning( f'we shouldn\'t get here' )
        resp = HttpResponse( 'problem; see logs' )
    return resp


# @shib_login
# def data_relationships( request, rltnshp_id=None ):
#     """ Called via ajax by views.edit_relationships() when `+` buton is clicked.
#         Url: '/data/relationships/' -- 'data_relationships_url' 
#         NOTE: 
#         - the response will be a redirect to the record (the "reference").
#         - the response.content will contain a json-string showing, eg, `{"relationship_id": 123, "new_relationship": true}`.
#         - the reason for the new_relationship boolean is to distinguish, in testing, whether the relationship was created or already-existing.
#         - as of 2023-June, the response.content is not being used by the front-end javascript.
#         """
#     log.debug( '\n\nstarting data_relationships()' )
#     log.debug( f'query_string, ``{request.META.get("QUERY_STRING", None)}``; rltnshp_id, ``{rltnshp_id}``; method, ``{request.method}``; payload, ``{request.body}``' )
#     user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
#     if request.method == 'POST':
#         log.debug( 'starting POST flow handling' )
#         relationship_dict: dict = v_data_relationships_manager.manage_relationships_post( request.body, user_id )
#         rfrnc_id = relationship_dict['rfrnc_id']; assert type(rfrnc_id) == int
#         relationship_id = relationship_dict['relationship_id']; assert type(relationship_id) == int
#         relationship_is_new = relationship_dict['relationship_is_new']; assert type(relationship_is_new) == bool
#         redirect_url = reverse( 'data_reference_relationships_url', kwargs={'rfrnc_id': rfrnc_id} )
#         log.debug( f'redirect_url, ```{redirect_url}```' )
#         # resp = HttpResponseRedirect( redirect_url )
#         # resp = HttpResponseRedirect( redirect_url, 'FOO2' )
#         content_json = json.dumps( relationship_dict )
#         resp = HttpResponseRedirect( redirect_to=redirect_url, content=content_json )
#     elif request.method == 'DELETE':
#         log.debug( 'starting DELETE flow handling' )
#         reference_id = request.GET['record']
#         log.debug( f'reference_id, ``{reference_id}``')
#         assert type(reference_id) == str
#         rfrnc_id: str = v_data_relationships_manager.manage_relationships_delete( rltnshp_id, reference_id, user_id )  # type: ignore
#         redirect_url = reverse( 'data_reference_relationships_url', kwargs={'rfrnc_id': rfrnc_id} )
#         resp = HttpResponseRedirect( redirect_url )
#     else:
#         log.warning( f'we shouldn\'t get here' )
#         resp = HttpResponse( 'problem; see logs' )
#     return resp


# @shib_login
# def data_relationships( request, rltnshp_id=None ):
#     """ Called via ajax by views.edit_relationships() when `+` buton is clicked.
#         Url: '/data/relationships/' -- 'data_relationships_url' 
#         NOTE: 
#         - the response will be a redirect to the record (the "reference").
#         - the response.content will contain a json-string showing, eg, `{"relationship_id": 123, "new_relationship": true}`.
#         - the reason for the new_relationship boolean is to distinguish, in testing, whether the relationship was created or already-existing.
#         - as of 2023-June, the response.content is not being used by the front-end javascript.
#         """
#     log.debug( '\n\nstarting data_relationships()' )
#     log.debug( f'query_string, ``{request.META.get("QUERY_STRING", None)}``; rltnshp_id, ``{rltnshp_id}``; method, ``{request.method}``; payload, ``{request.body}``' )
#     user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
#     if request.method == 'POST':
#         rfrnc_id: str = v_data_relationships_manager.manage_relationships_post( request.body, user_id )
#         redirect_url = reverse( 'data_reference_relationships_url', kwargs={'rfrnc_id': rfrnc_id} )
#         log.debug( f'redirect_url, ```{redirect_url}```' )
#         # resp = HttpResponseRedirect( redirect_url )
#         # resp = HttpResponseRedirect( redirect_url, 'FOO2' )
#         resp = HttpResponseRedirect( redirect_to=redirect_url, content='FOO4' )
#     elif request.method == 'DELETE':
#         rfrnc_id: str = v_data_relationships_manager.manage_relationships_delete( rltnshp_id, request.body, user_id )
#         redirect_url = reverse( 'data_reference_relationships_url', kwargs={'rfrnc_id': rfrnc_id} )
#         resp = HttpResponseRedirect( redirect_url )
#     else:
#         log.warning( f'we shouldn\'t get here' )
#         resp = HttpResponse( 'problem; see logs' )
#     return resp


# ===========================
# utility urls -- act as viewable integrity checks
# ===========================


@shib_login
def utility_citations( request ):
    """ Called manually to check data.
        Url: '/utility/documents/' -- 'utility_documents_url' """
    cites: dict = utility_manager.prep_citations_data()
    output = json.dumps( cites, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )


@shib_login
def utility_referents( request ):
    """ Called manually to check data.
        Url: '/utility/referents/' -- 'utility_referents_url' """
    referents: dict = utility_manager.prep_referents_data()
    output = json.dumps( referents, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )


# ===========================
# helper urls
# ===========================


def dnrmlzd_jsn_prx_url( request ):
    """ Allows ajax loading of json from old browse() view. """
    url = settings_app.DENORMALIZED_JSON_URL
    log.debug( f'url, ``{url}``' )
    r = requests.get( url )
    return HttpResponse( r.content, content_type='application/json; charset=utf-8' )


def browse_json_proxy( request ):
    """ Allows ajax loading of json from browse() view. """
    url = settings_app.BROWSE_JSON_URL
    log.debug( f'url, ``{url}``' )
    r = requests.get( url )
    return HttpResponse( r.content, content_type='application/json; charset=utf-8' )


# ===========================
# for development convenience
# ===========================


def version( request ):
    """ Returns basic data including branch & commit. """
    # log.debug( 'request.__dict__, ```%s```' % pprint.pformat(request.__dict__) )
    log.debug( f'project_settings, ``{pprint.pformat(project_settings)}``' )
    log.debug( f'debug-setting, ``{project_settings.DEBUG}``' )
    rq_now = datetime.datetime.now()
    commit = view_info_manager.get_commit()
    branch = view_info_manager.get_branch()
    info_txt = commit.replace( 'commit', branch )
    resp_now = datetime.datetime.now()
    taken = resp_now - rq_now
    context_dct = view_info_manager.make_context( request, rq_now, info_txt, taken )
    output = json.dumps( context_dct, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )


def error_check( request ):
    """ For an easy way to check that admins receive error-emails (in development).
        To view error-emails in runserver-development:
        - run, in another terminal window: `python -m smtpd -n -c DebuggingServer localhost:1026`,
        - (or substitue your own settings for localhost:1026)
    """
    log.debug( f'project_settings.DEBUG, ``{project_settings.DEBUG}``' )
    if project_settings.DEBUG == True:
        raise Exception( 'error-check triggered; admin emailed' )
    else:
        return HttpResponseNotFound( '<div>404 / Not Found</div>' )


# ===========================
# redesign urls
# ===========================


@shib_login
def redesign_home( request ):
    """ ? """
    # if project_settings.DEBUG == False:
    #     return HttpResponse( 'Not yet running on production.' )
    return HttpResponse( "What should be displayed here?" )


@shib_login
def redesign_citations( request ):
    """ 
    Displays main landing page of citations, with user's recently-edited citations first. 
    Note: if the html, non-json page is loaded, no data needs to be prepared, 
        because on page-load, javascript will make the 'data' call to get the json.
        So I'm only querying the db for data if the json is requested.
    """
    log.debug( '\n\nstarting redesign_citations()' )
    start_time = datetime.datetime.now()
    ## prep data ----------------------------------------------------
    if request.GET.get('format', '') == 'json':
        user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
        context: dict = view_editor_index_manager.query_documents( request.user.username, user_id )
        context['elapsed_time'] = str( datetime.datetime.now() - start_time )
    else:
        context = {}  # no data needed just to load the html-template -- which has javascript that will load the json``
    context['API_URL_ROOT'] = '%s://%s%s' % ( request.scheme, request.META.get('HTTP_HOST', '127.0.0.1'), reverse('data_root_url') )
    if request.user.is_authenticated:
        context['user_is_authenticated'] = True
        context['user_first_name'] = request.user.first_name
    ## prep response ------------------------------------------------
    if request.GET.get('format', '') == 'json':
        log.debug( 'building json response' )
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        log.debug( 'building template response' )
        resp = render( request, 'dashboard.html', context )
    return resp


# @shib_login
# def redesign_citations( request ):
#     """ Displays main landing page of citations, with user's recently-edited citations first. """
#     log.debug( '\n\nstarting redesign_citations()' )
#     start_time = datetime.datetime.now()
#     # if project_settings.DEBUG == False:
#     #     return HttpResponse( 'Not yet running on production.' )
#     user_id = request.user.profile.old_db_id if request.user.profile.old_db_id else request.user.id
#     context: dict = view_editor_index_manager.query_documents( request.user.username, user_id )
#     context['API_URL_ROOT'] = '%s://%s%s' % ( request.scheme, request.META.get('HTTP_HOST', '127.0.0.1'), reverse('data_root_url') )
#     context['elapsed_time'] = str( datetime.datetime.now() - start_time )
#     if request.user.is_authenticated:
#         context['user_is_authenticated'] = True
#         context['user_first_name'] = request.user.first_name
#     if request.GET.get('format', '') == 'json':
#         log.debug( 'building json response' )
#         resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
#     else:
#         log.debug( 'building template response' )
#         resp = render( request, 'redesign_citations.html', context )
#     return resp


@shib_login
def redesign_citation( request, cite_id=None ):
    """ Displays specific citation. """
    log.debug( '\n\nstarting redesign_citation()' )
    # if project_settings.DEBUG == False:
    #     return HttpResponse( 'Not yet running on production.' )

    if cite_id == None:
        return HttpResponseNotFound( '404 / Not Found' )

    # context: dict = view_edit_citation_manager.redesign_query_data( cite_id )
    ( scheme, host ) = ( request.scheme, request.META.get('HTTP_HOST', '127.0.0.1') )
    assert type(scheme) == str
    assert type(host) == str
    context: dict = view_edit_citation_manager.redesign_query_data( cite_id, scheme, host )
    assert type(context) in [dict, type(None)]  # context can be None if an id is entered that doesn't exist in the db
    if context == None:
        return HttpResponseNotFound( '404 / Not Found' )

    ## temp code to get P.R. location-data
    sess = view_edit_record_manager.make_session()
    location_context = view_edit_record_manager.prepare_common_data( sess )

    if request.user.is_authenticated:
        context['user_is_authenticated'] = True
        context['user_first_name'] = request.user.first_name
        context['location_stuff'] = location_context
    # log.debug( f'redesign_citation context, ```{pprint.pformat(context)}```' )
    if request.GET.get('format', '') == 'json':
        resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    else:
        resp = render( request, 'redesign_citation.html', context )
    return resp
