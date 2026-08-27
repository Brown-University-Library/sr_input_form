# -*- coding: utf-8 -*-

import datetime, json, logging, pprint, secrets, uuid

import requests
from disa_app import settings_app
from disa_app.lib import view_search_results_manager
from disa_app.models import UserProfile
from django.conf import settings as project_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from django.test import TestCase
from django.test.utils import override_settings


log = logging.getLogger(__name__)
TestCase.maxDiff = 1000


class Record_Test( TestCase ):
    """ Checks Record data-api urls. """

    def setUp(self):
        self.random_new_record_date = self.make_random_date_str()
        self.random_put_date = self.make_random_date_str()
        self.random_new_record_location = self.make_random_location_data()
        self.random_put_location = self.make_random_location_data()
        self.random_new_record_national_context = self.make_random_national_context()
        self.random_put_national_context = self.make_random_national_context()
        self.random_new_record_record_type = self.make_random_record_type()
        self.random_put_record_type = self.make_random_record_type()
        self.random_new_record_transcription_text = self.make_random_transcription()
        self.random_put_transcription = self.make_random_transcription()
        self.random_new_researcher_notes = self.make_random_researcher_notes()
        self.random_put_researcher_notes = self.make_random_researcher_notes()
        self.random_new_record_image_url = secrets.choice( [
            'https://foo1.com', 'https://foo2.com', 'https://foo3.com',
            None                                 # as shown below in create_new_record(), no key-value is sent if the field is not filled out
            ] )
        # self.random_put_record_text = secrets.choice( ['aaa', 'bbb', 'ccc', 'ddd'] )
        self.create_resp_statuscode = None  # updated by create_new_record()
        self.create_resp_dct = None         # updated by create_new_record()
        self.create_resp_id = None          # updated by create_new_record()
        self.delete_resp_statuscode = None  # updated by delete_new_record()
        # self.delete_resp_dct = None     # updated by delete_new_record()

    ## HELPERS ====================

    def create_new_record(self):
        """ Creates a record for tests. """
        post_url = reverse( 'data_record_url' )
        log.debug( f'post-url, ``{post_url}``' )
        payload = {
            'citation_id': 768,
            'date': self.random_new_record_date,                            # string; see self.random_new_record_date
            'locations': self.random_new_record_location,                   # list of dicts; see self.random_new_record_location
            'national_context': self.random_new_record_national_context,    # int
            'record_type': self.random_new_record_record_type,              # dict; see self.random_new_record_record_type
            'transcription': self.random_new_record_transcription_text,     # string
            'researcher_notes': self.random_new_researcher_notes            # string
            }
        if self.random_new_record_image_url:
            payload['image_url'] = self.random_new_record_image_url         # string; but no key-value data is sent if not filled-out
        log.debug( f'payload, ``{payload}``' )
        jsn = json.dumps( payload )
        response = self.client.post( post_url, data=jsn, content_type='application/json' )
        self.create_resp_statuscode = response.status_code
        self.post_resp_dct = json.loads( response.content )
        log.debug( f'create_new_record response dict, ``{self.post_resp_dct}``' )
        redirect_value = self.post_resp_dct['redirect']
        parts = redirect_value.split( '/' )
        self.create_resp_id = parts[-2]
        log.debug( f'create_resp_id, ``{self.create_resp_id}``' )
        # self.assertEqual( self.post_resp_id.isnumeric(), True )

    def delete_new_record(self):
        """ Deletes citation used by tests."""
        delete_url = reverse( 'data_reference_url', kwargs={'rfrnc_id': self.create_resp_id} )
        response = self.client.delete( delete_url )
        self.delete_resp_statuscode = response.status_code
        self.delete_resp_dct = json.loads( response.content )

    def make_random_date_str(self):
        """ Provides data for POST and PUT.
            Called by setUp() """
        dt_str =  secrets.choice( [  # month/day/year (future TODO: make this a more-standard ISO-format like year/month/day)
            '02/02/1492', '03/03/1493', '04/04/1494', ''
            ] )
        return dt_str

    def make_random_location_data(self):
        """ Provides data for POST and PUT.
            Called by setUp() """
        ''' Location can have 3, 2, 1, or 0 elements.
            - Position 1 will populate the form's 'Colony/State' field.
            - Position 2 will populate the form's 'Town' field.
            - Position 3 will populate the form's 'Additional location' field.'''
        loc = secrets.choice( [
            [ {'id': 735, 'label': 'Massachusetts', 'value': 'Massachusetts'},
              {'id': 21, 'label': 'Boston', 'value': 'Boston'},
              {'id': 357, 'label': 'somewhere about Pumpkin-Hill', 'value': 'somewhere about Pumpkin-Hill'}],
            [ {'id': 23, 'label': 'New York', 'value': 'New York'},
              {'id': 748, 'label': 'Albany', 'value': 'Albany'} ],
            [ {'id': 630, 'label': 'Rhode Island', 'value': 'Rhode Island'} ],
            [],  # this is what is sent if neither of the three location-fields are not filled out
            ] )
        return loc

    def make_random_national_context(self):
        """ Provides data for POST and PUT.
            Called by setUp() """
        nc = secrets.choice( [
            1, # British -- note: this is what is auto-sent if the field is not filled out
            2, # American
            3, # French
            4  # Spanish
            ] )
        return nc

    def make_random_record_type(self):
        """ Provides data for POST and PUT.
            Called by setUp() """
        rt = secrets.choice( [
            {'id': 29, 'label': 'Burial Record', 'value': 'Burial Record'},
            {'id': 1, 'label': 'Baptism', 'value': 'Baptism'},
            {'id': 20, 'label': 'Petition to Assembly', 'value': 'Petition to Assembly'},
            {'id': 0, 'label': '', 'value': ''}  # this is what is sent if the field is not filled out; the form will show "Unspecified"
            ] )
        return rt

    def make_random_transcription(self):
        """ Provides data for POST and PUT.
            Called by setUp() """
        t = secrets.choice( [
            'transcription_aaa', 'transcription_bbb', 'transcription_ccc',
            ''  # this is what is sent if the field is not filled out
            ] )
        return t

    def make_random_researcher_notes(self):
        """ Provides data for POST and PUT.
            Called by setUp() """
        rn = secrets.choice( [
            'researcher_notes_aaaa', 'researcher_notes_bbb', 'researcher_notes_ccc',
            ''  # this is what is sent if the field is not filled out
            ] )
        log.debug( f'rn, ``{rn}``' )
        log.debug( f'type(rn), ``{type(rn)}``' )
        return rn

    # def make_random_record_researcher_notes(self):
    #     """ Provides data for POST and PUT.
    #         Called by setUp() """
    #     rn = secrets.choice( [
    #         'researcher_notes_aaaa', 'researcher_notes_bbb', 'researcher_notes_ccc',
    #         ''  # this is what is sent if the field is not filled out
    #         ] )
    #     return rn

    # ## GET LIST ===================

    # TODO

    # ## GET SINGLE ===================

    # def test_get_single_bad(self):
    #     """ Checks bad GET of `http://127.0.0.1:8000/data/documents/foo`. """
    #     get_url = reverse( 'data_documents_url', kwargs={'doc_id': 'foo'} )
    #     log.debug( f'get_url, ``{get_url}``' )
    #     response = self.client.get( get_url )
    #     self.assertEqual( 404, response.status_code )
    #     self.assertEqual( b'404 / Not Found', response.content )

    def test_get_single_good(self):
        """ Checks good GET of `http://127.0.0.1:8000/data/records/abcd/`. """
        ## create record
        self.create_new_record()
        ## GET
        get_url = reverse( 'data_record_url', kwargs={'rec_id': self.create_resp_id} )
        log.debug( f'get_url, ``{get_url}``' )
        response = self.client.get( get_url )
        log.debug( f'response.content, ``{response.content}``' )
        ## tests
        self.assertEqual( 200, response.status_code )
        resp_dct = json.loads( response.content )
        self.assertEqual(
            ['entrants', 'groups', 'rec'],
            sorted(resp_dct.keys()) )
        record_keys = sorted( resp_dct['rec'].keys() )
        self.assertEqual(
            ['citation_fields', 'date', 'header', 'id', 'image_url', 'locations', 'national_context', 'record_type', 'researcher_notes', 'transcription'],
            record_keys )
        if self.random_new_record_date:
            date_object = datetime.datetime.strptime( self.random_new_record_date, '%m/%d/%Y')
            log.debug( f'initial date_object, ``{str(date_object)}``' )
            modified_date_string = f'{date_object.month}/{date_object.day}/{date_object.year}'
            log.debug( f'modified_date_string, ``{modified_date_string}``' )
            self.assertEqual(
                modified_date_string, resp_dct['rec']['date'] )
        if self.random_new_record_record_type['label'] == '':
            self.assertEqual(
                'Unspecified', resp_dct['rec']['header'] )
        else:
            self.assertEqual(
                self.random_new_record_record_type['label'], resp_dct['rec']['header'] )
        if self.random_new_record_image_url:
            self.assertEqual(
                self.random_new_record_image_url, resp_dct['rec']['image_url'] )
        self.assertEqual(
            self.random_new_record_location, resp_dct['rec']['locations'] )
        self.assertEqual(
            self.random_new_record_national_context, resp_dct['rec']['national_context'] )
        if self.random_new_record_record_type['label'] == '':
            self.assertEqual(
                {'id': 13, 'label': 'Unspecified', 'value': 'Unspecified'}, resp_dct['rec']['record_type'] )
        else:
            self.assertEqual(
                self.random_new_record_record_type, resp_dct['rec']['record_type'] )
        self.assertEqual(
            self.random_new_record_transcription_text, resp_dct['rec']['transcription'] )
        self.assertEqual(
            self.random_new_researcher_notes, resp_dct['rec']['researcher_notes'] )
        ## cleanup
        self.delete_new_record()

    # ## CREATE ====================

    # def test_post_bad(self):
    #     """ Checks `http://127.0.0.1:8000/data/records/` POST w/bad params. """
    #     post_url = reverse( 'data_record_url' )
    #     log.debug( f'post-url, ``{post_url}``' )
    #     payload = {
    #         'foo': 'bar'
    #     }
    #     response = self.client.post( post_url, payload )
    #     log.debug( f'create_new_record response (bytes), ``{response.content}``' )
    #     self.assertEqual( 400, response.status_code )
    #     self.assertEqual( b'400 / Bad Request', response.content )

    def test_post_good(self):
        """ Checks `http://127.0.0.1:8000/data/records/` POST w/good params. """
        ## create record
        self.create_new_record()
        ## tests
        self.assertEqual( 200, self.create_resp_statuscode )
        self.assertEqual( True, self.create_resp_id.isnumeric(),  )  # type: ignore
        self.assertEqual( str, type(self.create_resp_id) )
        self.assertEqual( ['redirect'], list(self.post_resp_dct.keys()) )
        ## cleanup
        self.delete_new_record()

    # ## UPDATE ====================

    # def test_put_bad(self):
    #     """ Checks bad PUT to `http://127.0.0.1:8000/data/records/foo/`. """
    #     put_url = reverse( 'data_record_url', kwargs={'doc_id': 'foo'} )
    #     put_response = self.client.put( put_url )
    #     self.assertEqual( 400, put_response.status_code )
    #     self.assertTrue( b'Bad Request' in put_response.content )

    def test_put_good(self):
        """ Checks good PUT to `http://127.0.0.1:8000/data/records/abcd/`.
            Sample put payload:
                {
                'citation_id': 768,
                'date': '03/03/1493',
                'locations': [
                    {'id': 735, 'label': 'Massachusetts', 'value': 'Massachusetts'},
                    {'id': 21, 'label': 'Boston', 'value': 'Boston'},
                    {'id': 357, 'label': 'somewhere about Pumpkin-Hill', 'value': 'somewhere about Pumpkin-Hill'}
                    ],
                'national_context': 1,
                'record_type': {
                    'id': 20,
                    'label': 'Petition to Assembly',
                    'value': 'Petition to Assembly'
                    },
                'researcher_notes': 'researcher_notes_ccc',
                'transcription': 'transcription_bbb'
                }
        """
        ## create citation
        self.create_new_record()
        ## PUT
        put_url = reverse( 'data_record_url', kwargs={'rec_id': self.create_resp_id} )
        log.debug( f'put_url-url, ``{put_url}``' )
        put_payload = {
            'citation_id': 768,
            'date': self.random_put_date,
            'locations': self.random_put_location,
            'national_context': self.random_put_national_context,
            'record_type': self.random_put_record_type,
            'transcription': self.random_put_transcription,
            'researcher_notes': self.random_put_researcher_notes,
            'record_citation_fields': { '67': 'test-1', '105': 'test-2' }
            }
        jsn = json.dumps( put_payload )
        put_response = self.client.put( put_url, data=jsn, content_type='application/json' )
        put_resp_dct = json.loads( put_response.content )
        log.debug( f'put_resp_dct, ``{pprint.pformat(put_resp_dct)}``' )
        ## tests
        ''' Note, these are similar to the GET tests. '''
        self.assertEqual( 200, put_response.status_code )
        self.assertEqual(
            ['rec'], sorted(put_resp_dct.keys()) )
        rec_keys = sorted( put_resp_dct['rec'].keys() )
        log.debug( f'rec_keys, ``{rec_keys}``' )
        self.assertEqual(  # similar to POST payload, except that has a key of `citation_id` instead of `citation`, and this has an `id` element.
            ['citation', 'date', 'id', 'locations', 'national_context', 'record_type', 'researcher_notes', 'transcription' ],
            sorted(rec_keys) )
        if self.random_put_date:
            date_object = datetime.datetime.strptime( self.random_put_date, '%m/%d/%Y')
            log.debug( f'initial date_object, ``{str(date_object)}``' )
            modified_date_string = f'{date_object.month}/{date_object.day}/{date_object.year}'
            log.debug( f'modified_date_string, ``{modified_date_string}``' )
            self.assertEqual(
                modified_date_string, put_resp_dct['rec']['date'] )
        self.assertEqual(
            self.random_put_location, put_resp_dct['rec']['locations'] )
        self.assertEqual(
            self.random_put_national_context, put_resp_dct['rec']['national_context'] )
        if self.random_put_record_type['label'] == '':
            self.assertEqual(
                {'id': 13, 'label': 'Unspecified', 'value': 'Unspecified'}, put_resp_dct['rec']['record_type'] )
        else:
            self.assertEqual(
                self.random_put_record_type, put_resp_dct['rec']['record_type'] )
        self.assertEqual(
            self.random_put_transcription, put_resp_dct['rec']['transcription'] )
        self.assertEqual(
            self.random_put_researcher_notes, put_resp_dct['rec']['researcher_notes'] )
        ## cleanup
        self.delete_new_record()

        ## end of def test_put_good()

    # ## DELETE ====================

    # def test_delete_bad(self):
    #     """ Checks bad DELETE of `http://127.0.0.1:8000/data/reference/foo/`. """
    #     ## DELETE
    #     self.post_resp_id == 'foo'
    #     self.delete_new_record()  # will attempt to delete record-id `foo`
    #     ## tests
    #     self.assertEqual( 500, self.delete_resp_statuscode )
    #     self.assertEqual( b'500 / Server Error', self.delete_resp_content )

    def test_delete_good(self):
        """ Checks good DELETE of `http://127.0.0.1:8000/data/reference/abcd/`.
            Note that, for no good reason, this root url is _different_ from the normal `http://127.0.0.1:8000/data/records/abcd/` """
        ## create record
        self.create_new_record()
        log.debug( 'created new record' )
        ## DELETE
        self.delete_new_record()
        log.debug( 'deleted new record' )
        ## tests
        self.assertEqual( 200, self.delete_resp_statuscode )
        self.assertEqual(
            # {'redirect': '/editor/documents/768/'},
            {'redirect': '/redesign_citations/768/'},
            self.delete_resp_dct )  # for now, we're hard-coding new adds to citation-document #768

    ## end Record_Test()
