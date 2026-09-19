# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint, uuid

import sqlalchemy
from disa_app import models_sqlalchemy as models_alch
from disa_app import settings_app
from disa_app.lib import person_common
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseServerError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


log = logging.getLogger(__name__)


def make_session() -> sqlalchemy.orm.session.Session:
    engine = create_engine( settings_app.DB_URL, echo=True )
    Session = sessionmaker( bind=engine )
    session = Session()
    return session


class Getter():
    def __init__( self ):
        self.session = None

    def manage_get( self, rfrnt_id: str ) -> HttpResponse:
        """ Manages data/api ajax 'GET'.
            Called by views.data_entrants(), which is triggered by views.edit_person() webpage.
            TODO: handle 'not-found' (returns None) on referent lookup. """
        log.debug( 'starting manage_get' )
        log.debug( f'rfrnt_id, ```{rfrnt_id}```' )
        self.session = make_session()
        try:
            rfrnt: models_sqlalchemy.Referent = self.session.query( models_alch.Referent ).get( rfrnt_id )
            log.debug( f'rfrnt.__dict__, ``{pprint.pformat(rfrnt.__dict__)}``' )
            context: dict = self.prep_get_response( rfrnt )
            resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
        except:
            msg = 'Not Found -- possible problem with update, or with response-prep; see logs'
            log.exception( msg )
            resp = HttpResponseNotFound( msg )
        log.debug( 'returning response' )
        return resp

    def prep_get_response( self, rfrnt: models_alch.Referent ) -> dict:
        """ Prepares context.
            Called by manage_get() """
        data = { 'ent': {} }
        data['ent']['id'] = rfrnt.id
        data['ent']['uuid'] = rfrnt.uuid
        data['ent']['names'] = [
            { 'first': n.first, 'last': n.last,
                'name_type': n.name_type.name,
                'id': n.id } for n in rfrnt.names ]
        data['ent']['age_text'] = rfrnt.age
        data['ent']['age_number'] = rfrnt.age_number
        data['ent']['age_category'] = rfrnt.age_category
        data['ent']['sex'] = rfrnt.sex
        data['ent']['races'] = [
            { 'label': r.name, 'value': r.name,
                'id': r.name } for r in rfrnt.races ]
        data['ent']['race_text'] = rfrnt.race_text
        data['ent']['tribes'] = [
            { 'label': t.name, 'value': t.name,
                'id': t.name } for t in rfrnt.tribes ]
        data['ent']['origins'] = [
            { 'label': o.name, 'value': o.name,
                'id': o.name } for o in rfrnt.origins ]
        data['ent']['titles'] = [
            { 'label': t.name, 'value': t.name,
                'id': t.name } for t in rfrnt.titles ]
        data['ent']['vocations'] = [
            { 'label': v.name, 'value': v.name,
                'id': v.name } for v in rfrnt.vocations ]
        data['ent']['occupation_text'] = rfrnt.occupation_text
        data['ent']['enslavements'] = [
            { 'label': e.name, 'value': e.name,
                'id': e.name } for e in rfrnt.enslavements ]
        log.debug( f'data, ```{pprint.pformat(data)}```' )
        return data

    ## end class Getter()


class Updater():

    def __init__( self ):
        self.session = None  # updated by manage_put()
        self.common = None   # updated by manage_put()

    # def manage_put( self, payload: bytes, request_user_id: int, rfrnt_id: str ) -> HttpResponse:
    #     """ Manages data/api ajax 'PUT'.
    #         Called by views.data_entrants(), triggered by views.edit_record() webpage. """
    #     log.debug( 'starting manage_put()' )
    #     self.session = make_session()
    #     self.common = Common()
    #     data: dict = json.loads( payload )
    #     try:
    #         context: dict = self.execute_update( request_user_id, data, rfrnt_id )
    #         resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
    #     except:
    #         msg = 'problem with update, or with response-prep; see logs'
    #         log.exception( msg )
    #         resp = HttpResponse( msg )
    #     log.debug( 'returning response' )
    #     return resp

    def manage_put( self, payload: bytes, request_user_id: int, rfrnt_id: str ) -> HttpResponse:
        """ Manages data/api ajax 'PUT'.
            Called by views.data_entrants(), triggered by views.edit_record() webpage. """
        log.debug( 'starting manage_put()' )
        assert type(payload) == bytes
        assert type(request_user_id) == int
        assert type(rfrnt_id) == str
        self.session = make_session()
        self.common = Common()
        try:
            data: dict = json.loads( payload )
            log.debug( f'data, ``{pprint.pformat(data)}``' )
            assert sorted( data.keys() ) == ['id', 'name', 'record_id', 'roles']
        except:
            msg = 'Bad Request -- problem with put; see logs'
            log.exception( msg )
            return HttpResponseBadRequest( msg )
        try:
            context: dict = self.execute_update( request_user_id, data, rfrnt_id )
            resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
        except:
            msg = 'Server Error -- problem with update, or with response-prep; see logs'
            log.exception( msg )
            resp = HttpResponseServerError( msg )
        log.debug( 'returning response' )
        return resp

    def execute_update( self, user_id: int, data: dict, rfrnt_id: str ) -> dict:
        """ Updates db and returns data.
            Called by manage_put() """
        rnt: models_sqlalchemy.Referent = self.session.query( models_alch.Referent ).get( rfrnt_id )
        primary_name: str = self.common.update_referent_name( data['name'], self.session )
        rnt.names.append( primary_name )
        rnt.primary_name = primary_name
        rnt.roles = [ self.common.get_or_create_referent_attribute(a, models_alch.Role, self.session) for a in data['roles'] ]
        self.session.add( rnt )
        self.session.commit()
        self.common.stamp_edit( user_id, rnt.reference, self.session )
        data = self.common.prep_put_post_response_data( rnt )
        log.debug( f'returning data, ```{pprint.pformat(data)}```' )
        return data

    ## end class Updater()


class Details_Updater():

    def __init__( self ):
        """ Updated by manage_details_update() """
        self.session = None
        self.common = None

    def manage_details_put( self, payload: bytes, request_user_id: int, rfrnt_id: str ) -> dict:
        """ Manages data/api ajax 'PUT'.
            Called by views.data_entrants_details(), triggered by views.edit_person() webpage. """
        log.debug( 'starting manage_details_put' )
        log.debug( f'payload, ``{payload}``' )
        log.debug( f'request_user_id, ``{request_user_id}``' )
        log.debug( f'rfrnt_id, ``{rfrnt_id}``' )
        self.session = make_session()
        self.common = Common()
        try:
            data: dict = json.loads( payload )
            # log.debug( f'details-put-dct, ``{pprint.pformat(data)}``' )
            context: dict = self.execute_details_update( request_user_id, data, rfrnt_id )
        except:
            msg = 'problem with details-update, or with response-prep; see logs'
            log.exception( msg )
            # resp = HttpResponse( msg )
            context: dict = { 'problem': msg }
        log.debug( 'returning response' )
        # return resp
        return context

    def execute_details_update( self, user_id: int, data: dict, rfrnt_id: str ) -> dict:
        """ Updates db and returns data.
            Called by manage_details_put() """
        log.debug( 'starting execute_details_update()' )
        print( '------- starting execute_details_update()' )
        log.debug( f'submitted user_id, ``{user_id}``' )
        log.debug( f'submitted data, ``{data}``' )
        log.debug( f'submitted rfrnt_id, ``{rfrnt_id}``' )
        rfrnt: models_alch.Referent = self.session.query( models_alch.Referent ).get( rfrnt_id )
        log.debug( f'initial rfrnt.dictify(), ``{pprint.pformat(rfrnt.dictify())}``' )
        rfrnt.names = [ self.common.update_referent_name( na, self.session )
            for na in data['names'] ]
        log.debug( f'rfrnt.names, ``{rfrnt.names}``' )
        rfrnt.age = data['age_text']
        rfrnt.age_number = data['age_number']
        rfrnt.age_category = data['age_category']
        rfrnt.sex = data['sex']
        rfrnt.primary_name = rfrnt.names[0]
        rfrnt.races = [ self.common.get_or_create_referent_attribute( ra, models_alch.Race, self.session )
            for ra in data['races'] ]
        rfrnt.race_text = data['race_text']
        rfrnt.tribes = [ self.common.get_or_create_referent_attribute( tr, models_alch.Tribe, self.session )
            for tr in data['tribes'] ]
        rfrnt.origins = [ self.common.get_or_create_referent_attribute( ori, models_alch.Location, self.session )
            for ori in data['origins'] ]
        rfrnt.titles = [ self.common.get_or_create_referent_attribute( ti, models_alch.Title, self.session )
            for ti in data['titles'] ]
        rfrnt.enslavements = [ self.common.get_or_create_referent_attribute( st, models_alch.EnslavementType, self.session )
            for st in data['statuses'] ]
        log.debug( f'rfrnt.enslavements from statuses-data, ``{rfrnt.enslavements}``' )
        rfrnt.vocations = [ self.common.get_or_create_referent_attribute( vo, models_alch.Vocation, self.session )
            for vo in data['vocations'] ]
        rfrnt.occupation_text = data['occupation_text']
        try:
            self.session.add( rfrnt )
            log.debug( 'session.add ok' )
        except:
            log.exception( 'problem with session.add(); traceback follows but processing continues' )
        try:
            self.session.commit()
            log.debug( 'session.commit ok' )
        except:
            log.exception( 'problem with session.commit(); traceback follows but processing continues' )
        try:
            self.common.stamp_edit( user_id, rfrnt.reference, self.session )
            log.debug( 'common.stamp_edit() ok' )
        except:
            log.exception( 'problem with common.stamp_edit(); traceback follows but processing continues' )
        log.debug( f'final rfrnt.dictify() after add & commit & stamp, ``{pprint.pformat(rfrnt.dictify())}``' )
        data = { 'redirect': reverse( 'edit_record_w_recid_url', kwargs={'rec_id': rfrnt.reference_id} ) }
        log.debug( f'returning data, ```{pprint.pformat(data)}```' )
        print( '------- ending execute_details_update()' )
        return data

    ## end class Details_Updater()


class Poster():

    def __init__( self ):
        """ Updated by manage_post() """
        self.session = None
        self.common = None

    def manage_post( self, payload: bytes, request_user_id: int, rfrnt_id: str ) -> HttpResponse:
        """ Manages data/api ajax 'POST'.
            Called by views.data_entrants(), triggered by views.edit_record() webpage 'Add person' button save. """
        log.debug( 'starting manage_post' )
        assert type(payload) == bytes
        assert type(request_user_id) == int
        assert type(rfrnt_id) == str  # will be 'new'
        log.debug( f'rfrnt_id, ``{rfrnt_id}``' )
        self.session = make_session()
        self.common = Common()
        try:
            data: dict = json.loads( payload )
            log.debug( f'data, ``{pprint.pformat(data)}``' )
            assert sorted( data.keys() ) == ['id', 'name', 'record_id', 'roles']
        except:
            msg = 'Bad Request -- problem with post; see logs'
            log.exception( msg )
            return HttpResponseBadRequest( msg )
        try:
            context: dict = self.execute_post( request_user_id, data )
            resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
        except:
            msg = 'Server Error -- problem with response-prep; see logs'
            log.exception( msg )
            resp = HttpResponseServerError( msg )
        log.debug( 'returning response' )
        return resp

    def execute_post( self, user_id: int, data: dict ) -> dict:
        """ Updates db and returns data.
            Called by manage_post() """
        prs = self.initialize_person()
        rfrnt = models_alch.Referent( reference_id=data['record_id'] )
        rfrnt.uuid = uuid.uuid4().hex
        rfrnt.person = prs
        primary_name: str = self.common.update_referent_name( data['name'], self.session )
        rfrnt.names.append( primary_name )
        rfrnt.primary_name = primary_name
        prs.first_name = primary_name.first
        prs.last_name = primary_name.last
        self.session.add( prs )
        rfrnt.roles = [ self.common.get_or_create_referent_attribute(a, models_alch.Role, self.session) for a in data['roles'] ]
        self.session.add( rfrnt )
        self.session.commit()
        self.common.stamp_edit( user_id, rfrnt.reference, self.session )
        data = self.common.prep_put_post_response_data( rfrnt )
        log.debug( f'returning data, ```{pprint.pformat(data)}```' )
        return data

    def initialize_person( self ) -> models_alch.Person:
        """ Creates person record.
            Called by execute_post() """
        prs = models_alch.Person()
        self.session.add( prs )
        self.session.commit()
        log.debug( f'returning prs, ```{prs}```' )
        return prs

    ## end class Poster()


class Deleter():

    def __init__( self ):
        """ Updated by manage_post() """
        self.session = None
        self.common = None

    def manage_delete( self, request_user_id: int, rfrnt_id: str ) -> HttpResponse:
        """ Manages data/api ajax 'POST'.
            Called by views.data_entrants(), triggered by views.edit_record() webpage 'Add person' button save. """
        log.debug( 'starting manage_delete' )
        assert type(request_user_id) == int
        assert type(rfrnt_id) == str
        self.session = make_session()
        self.common = Common()
        try:
            context: dict = self.execute_delete( request_user_id, rfrnt_id )
            resp = HttpResponse( json.dumps(context, sort_keys=True, indent=2), content_type='application/json; charset=utf-8' )
        except:
            msg = 'Server Error -- problem with delete, or with response-prep; see logs'
            log.exception( msg )
            resp = HttpResponseServerError( msg )
        log.debug( 'returning response' )
        return resp

    def execute_delete( self, user_id: int, rfrnt_id: str ) -> dict:
        """ Deletes given referent and associated data.
            Called by manage_delete() """
        rfrnt: models_sqlalchemy.Referent = self.session.query( models_alch.Referent ).get( rfrnt_id )
        rfrnc: models_sqlalchemy.Reference = rfrnt.reference
        rels_as_sbj = self.session.query( models_alch.ReferentRelationship ).filter_by( subject_id=rfrnt.id ).all()
        rels_as_obj = self.session.query( models_alch.ReferentRelationship ).filter_by( object_id=rfrnt.id ).all()
        for r in rels_as_sbj:
            self.session.delete( r )
        for r in rels_as_obj:
            self.session.delete( r )
        self.session.delete( rfrnt )
        self.session.commit()
        self.common.stamp_edit( user_id, rfrnc, self.session )
        data = { 'id': rfrnt_id }
        log.debug( f'data, ```{data}```' )
        return data

    ## end class Deleter()


class Common():
    """ Contains entrant-manager functions used by multiple method-classes. """

    def __init__( self ):
        pass

    def update_referent_name( self, data: dict, session: sqlalchemy.orm.session.Session ) -> models_alch.ReferentName:
        """ Obtains a ReferentName object. Does not write to the db.
            Called by Updater.execute_update() and Poster.manage_post() """
        log.debug( f'data, ```{data}```' )
        if data['id'] == 'name': # what's this 'id' for??
            name = models_alch.ReferentName()
            log.debug( f'name from data-id, ```{name}```' )
        else:
            name = session.query( models_alch.ReferentName ).get( data['id'] )
            log.debug( f'name not from data-id, ```{name}```' )
        name.first = data['first']
        name.last = data['last']
        given = session.query( models_alch.NameType ).filter_by( name='Given' ).first()
        # name.name_type_id: int = data.get('name_type', given.id)
        temp_name_type_id: int = data.get('name_type', given.id)
        name.name_type_id = temp_name_type_id
        log.debug( 'returning name' )
        return name

    def get_or_create_referent_attribute( self, data: dict, attrModel: models_alch.Role, session: sqlalchemy.orm.session.Session ) -> models_alch.Role:
        """ Obtains, or creates and obtains, and then returns, a models_alch.Role instance.
            Called by Updater.execute_update() and Poster.manage_post() """
        existing: models_alch.Role = session.query( attrModel ).filter_by( name=data['name'] ).first()  # or None, I think
        if not existing:
            new_attr: models_alch.Role = attrModel( name=data['name'] )
            session.add( new_attr )
            session.commit()
            log.debug( f'new_attr, ```{new_attr}```' )
            return new_attr
        else:
            log.debug( f'existing, ```{existing}```' )
            return existing

    def stamp_edit( self, request_user_id: int, reference_obj: models_alch.Reference, session: sqlalchemy.orm.session.Session ) -> None:
        """ Updates when the Reference-object was last edited and by whom.
            Called by Updater.execute_update() and Poster.manage_post() """
        log.debug( 'starting stamp_edit()' )
        edit = models_alch.ReferenceEdit( reference_id=reference_obj.id, user_id=request_user_id, timestamp=datetime.datetime.utcnow() )
        session.add( edit )
        session.commit()
        return

    def prep_put_post_response_data( self, rfrnt: models_alch.Referent ) -> dict:
        """ Prepares dct for json response.
            Called by Updater.execute_update() and Poster.manage_post() """
        data = {
            'name_id': rfrnt.primary_name.id,
            'first': rfrnt.primary_name.first,
            'last': rfrnt.primary_name.last,
            'id': rfrnt.id,
            'uuid': rfrnt.uuid,
            'person_id': rfrnt.person_id,
            'roles': [ role.id for role in rfrnt.roles ]
            }
        log.debug( f'data, ```{pprint.pformat( data )}```' )
        return data

    ## end class Common()


## from DISA -- '/data/entrants/details/' -- PUT
# @app.route('/data/entrants/details/', methods=['PUT'])
# @app.route('/data/entrants/details/<rntId>', methods=['PUT'])
# @login_required
# def update_referent_details(rntId):
#     rnt = models.Referent.query.get(rntId)
#     data = request.get_json()
#     rnt.names = [ update_referent_name(n) for n in data['names'] ]
#     rnt.age = data['age']
#     rnt.sex = data['sex']
#     rnt.primary_name = rnt.names[0]
#     rnt.races = [ get_or_create_referent_attribute(a, models.Race)
#         for a in data['races'] ]
#     rnt.tribes = [ get_or_create_referent_attribute(a, models.Tribe)
#         for a in data['tribes'] ]
#     rnt.origins = [ get_or_create_referent_attribute(a, models.Location)
#         for a in data['origins'] ]
#     rnt.titles = [ get_or_create_referent_attribute(a, models.Title)
#         for a in data['titles'] ]
#     rnt.enslavements = [ get_or_create_referent_attribute(
#         a, models.EnslavementType)
#             for a in data['statuses'] ]
#     rnt.vocations = [ get_or_create_referent_attribute(
#         a, models.Vocation)
#             for a in data['vocations'] ]
#     db.session.add(rnt)
#     db.session.commit()

#     stamp_edit(current_user, rnt.reference)

#     return jsonify(
#         { 'redirect': url_for('edit_record', recId=rnt.reference_id) })


## from DISA -- '/data/entrants/' -- GET
# @app.route('/data/entrants/', methods=['GET'])
# @app.route('/data/entrants/<rntId>', methods=['GET'])
# @login_required
# def read_referent_data(rntId=None):
#     data = { 'ent': {} }
#     if rntId == None:
#         return jsonify(data)
#     rnt = models.Referent.query.get(rntId)
#     data['ent']['id'] = rnt.id
#     data['ent']['names'] = [
#         { 'first': n.first, 'last': n.last,
#             'name_type': n.name_type.name,
#             'id': n.id } for n in rnt.names ]
#     data['ent']['age'] = rnt.age
#     data['ent']['sex'] = rnt.sex
#     data['ent']['races'] = [
#         { 'label': r.name, 'value': r.name,
#             'id': r.name } for r in rnt.races ]
#     data['ent']['tribes'] = [
#         { 'label': t.name, 'value': t.name,
#             'id': t.name } for t in rnt.tribes ]
#     data['ent']['origins'] = [
#         { 'label': o.name, 'value': o.name,
#             'id': o.name } for o in rnt.origins ]
#     data['ent']['titles'] = [
#         { 'label': t.name, 'value': t.name,
#             'id': t.name } for t in rnt.titles ]
#     data['ent']['vocations'] = [
#         { 'label': v.name, 'value': v.name,
#             'id': v.name } for v in rnt.vocations ]
#     data['ent']['enslavements'] = [
#         { 'label': e.name, 'value': e.name,
#             'id': e.name } for e in rnt.enslavements ]
#     return jsonify(data)


## from DISA -- '/data/entrants/' -- PUT / POST / DELETE
# @app.route('/data/entrants/', methods=['POST'])
# @app.route('/data/entrants/<rntId>', methods=['PUT', 'DELETE'])
# @login_required
# def update_referent(rntId=None):
#     if request.method == 'DELETE':
#         rnt = models.Referent.query.get(rntId)
#         ref = rnt.reference
#         rels_as_sbj = models.ReferentRelationship.query.filter_by(
#             subject_id=rnt.id).all()
#         rels_as_obj = models.ReferentRelationship.query.filter_by(
#             object_id=rnt.id).all()
#         for r in rels_as_sbj:
#             db.session.delete(r)
#         for r in rels_as_obj:
#             db.session.delete(r)
#         db.session.delete(rnt)
#         db.session.commit()

#         stamp_edit(current_user, ref)

#         return jsonify( { 'id': rntId } )
#     data = request.get_json()
#     if request.method == 'POST':
#         prs = models.Person()
#         db.session.add(prs)
#         db.session.commit()
#         rnt = models.Referent(reference_id=data['record_id'])
#         rnt.person = prs
#     if request.method == 'PUT':
#         rnt = models.Referent.query.get(rntId)
#     primary_name = update_referent_name(data['name'])
#     rnt.names.append(primary_name)
#     rnt.primary_name = primary_name
#     if request.method == 'POST':
#         prs.first_name = primary_name.first
#         prs.last_name = primary_name.last
#         db.session.add(prs)
#     rnt.roles = [ get_or_create_referent_attribute(a, models.Role)
#         for a in data['roles'] ]
#     db.session.add(rnt)
#     db.session.commit()

#     stamp_edit(current_user, rnt.reference)

#     return jsonify({
#         'name_id': rnt.primary_name.id,
#         'first': rnt.primary_name.first,
#         'last': rnt.primary_name.last,
#         'id': rnt.id,
#         'person_id': rnt.person_id,
#         'roles': [ role.id for role in rnt.roles ] })
