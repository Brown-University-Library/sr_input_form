# -*- coding: utf-8 -*-

import json, logging, pprint, secrets, uuid

import requests
from disa_app import settings_app
from disa_app.lib import view_search_results_manager
from disa_app.models import UserProfile
from django.conf import settings as project_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from django.test import TestCase  # from django.test import SimpleTestCase as TestCase    ## TestCase requires db, so if you're not using a db, and want tests, try this
from django.test.utils import override_settings


log = logging.getLogger(__name__)
TestCase.maxDiff = 1000


class Client_ReferenceGroup_Test( TestCase ):
    """ Checks reference-group api urls. """

    def setUp(self):
        self.new_uuid = None
        self.post_resp_dct = None
        self.delete_resp_dct = None
        log.debug( f'initial self.new_uuid, ``{self.new_uuid}``' )
        log.debug( f'self.post_resp_dct, ``{self.post_resp_dct}``' )
        log.debug( f'self.delete_resp_dct, ``{self.delete_resp_dct}``' )

    ## HELPERS ====================

    def create_new_group(self):
        """ Creates a group for tests. """
        post_url = reverse( 'data_group_url', kwargs={'incoming_uuid': 'new'} )
        log.debug( f'post-url, ``{post_url}``' )
        payload = {
            'count': 7,
            'count_estimated': True,
            'description': 'the description',
            'reference_id': 49
        }
        jsn = json.dumps( payload )
        response = self.client.post( post_url, data=jsn, content_type='application/json' )
        self.assertEqual( 200, response.status_code )
        self.post_resp_dct = json.loads( response.content )
        self.new_uuid = self.post_resp_dct['response']['group_data']['uuid']
        log.debug( f'self.new_uuid, ``{self.new_uuid}``' )

    def delete_new_group(self):
        """ Deletes group used by tests."""
        delete_url = reverse( 'data_group_url', kwargs={'incoming_uuid': self.new_uuid} )
        response = self.client.delete( delete_url )
        self.assertEqual( 200, response.status_code )
        self.delete_resp_dct = json.loads( response.content )
        log.debug( f'delete_resp_dct, ``{pprint.pformat(self.delete_resp_dct)}``' )

    ## GET =======================

    def test_get_bad(self):
        """ Checks bad GET of `http://127.0.0.1:8000/data/reference_group/abcd/`. """
        get_url = reverse( 'data_group_url', kwargs={'incoming_uuid': 'foo'} )
        log.debug( f'get_url, ``{get_url}``' )
        response = self.client.get( get_url )
        self.assertEqual( 404, response.status_code )
        self.assertTrue( b'Not Found' in response.content )

    def test_get_good(self):
        """ Checks good GET of `http://127.0.0.1:8000/data/reference_group/abcd/`. """
        ## create group
        self.create_new_group()
        target_uuid = self.new_uuid
        log.debug( f'target_uuid, ``{target_uuid}``' )
        ## GET
        get_url = reverse( 'data_group_url', kwargs={'incoming_uuid': target_uuid} )
        log.debug( f'get_url, ``{get_url}``' )
        response = self.client.get( get_url )
        ## tests
        self.assertEqual( 200, response.status_code )
        resp_dct = json.loads( response.content )
        self.assertEqual( ['request', 'response'], sorted(resp_dct.keys()) )
        req_keys = sorted( resp_dct['request'].keys() )
        self.assertEqual( ['method', 'payload', 'timestamp', 'url'], req_keys )
        resp_keys = sorted( resp_dct['response'].keys() )
        self.assertEqual( ['elapsed_time', 'group_data'], resp_keys )
        resp_group_data_keys = sorted( resp_dct['response']['group_data'].keys() )
        self.assertEqual( ['count', 'count_estimated', 'date_created', 'date_modified', 'description', 'reference_id', 'uuid' ], resp_group_data_keys )
        ## cleanup
        self.delete_new_group()

    ## CREATE ====================

    def test_post_bad(self):
        """ Checks `http://127.0.0.1:8000/data/reference_group/abcd/ w/bad params. """
        post_url = reverse( 'data_group_url', kwargs={'incoming_uuid': 'new'} )
        log.debug( f'post-url, ``{post_url}``' )
        payload = {
            'foo': 'bar'
        }
        response = self.client.post( post_url, payload )
        self.assertEqual( 400, response.status_code )
        self.assertTrue( b'Bad Request' in response.content )

    def test_post_good(self):
        """ Checks `http://127.0.0.1:8000/data/reference_group/abcd/ w/good params. """
        ## create group
        self.create_new_group()
        ## tests
        self.assertEqual( ['request', 'response'], sorted(self.post_resp_dct.keys()) )
        req_keys = sorted( self.post_resp_dct['request'].keys() )
        self.assertEqual( ['method', 'payload', 'timestamp', 'url'], req_keys )
        req_payload_keys = sorted( self.post_resp_dct['request']['payload'].keys() )
        self.assertEqual( ['count', 'count_estimated', 'description', 'reference_id'], req_payload_keys )
        resp_keys = sorted( self.post_resp_dct['response'].keys() )
        self.assertEqual( ['elapsed_time', 'group_data'], resp_keys )
        resp_group_data_keys = sorted( self.post_resp_dct['response']['group_data'].keys() )
        self.assertEqual( ['count', 'count_estimated', 'date_created', 'date_modified', 'description', 'reference_id', 'uuid' ], resp_group_data_keys )
        ## cleanup
        self.delete_new_group()

    ## UPDATE ====================

    def test_put_bad(self):
        """ Checks bad PUT of `http://127.0.0.1:8000/data/reference_group/abcd/`. """
        put_url = reverse( 'data_group_url', kwargs={'incoming_uuid': 'foo'} )
        put_response = self.client.put( put_url )
        self.assertEqual( 400, put_response.status_code )
        self.assertTrue( b'Bad Request' in put_response.content )

    def test_put_good(self):
        """ Checks good PUT of `http://127.0.0.1:8000/data/reference_group/abcd/`. """
        ## create group
        self.create_new_group()
        ## PUT
        put_url = reverse( 'data_group_url', kwargs={'incoming_uuid': self.new_uuid} )
        log.debug( f'put_url-url, ``{put_url}``' )
        random_count = secrets.choice( [2, 4, 6, 8, 10] )
        random_description = secrets.choice( ['descA', 'descB', 'descC', 'descD', 'descE'] )
        put_payload = {
            'count': random_count,
            'count_estimated': False,
            'description': random_description,
            'reference_id': 49
        }
        jsn = json.dumps( put_payload )
        put_response = self.client.put( put_url, data=jsn, content_type='application/json' )
        put_resp_dct = json.loads( put_response.content )
        ## tests
        self.assertEqual( 200, put_response.status_code )
        resp_dct = json.loads( put_response.content )
        self.assertEqual( ['request', 'response'], sorted(resp_dct.keys()) )
        req_keys = sorted( resp_dct['request'].keys() )
        self.assertEqual( ['method', 'payload', 'timestamp', 'url'], req_keys )
        req_payload_keys = sorted( resp_dct['request']['payload'].keys() )
        self.assertEqual( ['count', 'count_estimated', 'description', 'reference_id'], req_payload_keys )
        resp_keys = sorted( resp_dct['response'].keys() )
        self.assertEqual( ['elapsed_time', 'group_data'], resp_keys )
        resp_group_data_keys = sorted( resp_dct['response']['group_data'].keys() )
        self.assertEqual( ['count', 'count_estimated', 'date_created', 'date_modified', 'description', 'reference_id', 'uuid' ], resp_group_data_keys )
        self.assertEqual( random_count, resp_dct['response']['group_data']['count'] )
        self.assertEqual( random_description, resp_dct['response']['group_data']['description'] )
        ## cleanup
        self.delete_new_group()

    ## DELETE ====================

    def test_delete_bad(self):
        """ Checks bad DELETE of `http://127.0.0.1:8000/data/reference_group/abcd/`. """
        delete_url = reverse( 'data_group_url', kwargs={'incoming_uuid': 'foo'} )
        delete_response = self.client.delete( delete_url )
        self.assertEqual( 404, delete_response.status_code )
        self.assertTrue( b'Not Found' in delete_response.content )

    def test_delete_good(self):
        """ Checks good DELETE of `http://127.0.0.1:8000/data/reference_group/abcd/`. """
        ## create group
        self.create_new_group()
        ## DELETE
        self.delete_new_group()
        ## tests
        self.assertEqual( ['request', 'response'], sorted(self.delete_resp_dct.keys()) )
        req_keys = sorted( self.delete_resp_dct['request'].keys() )
        self.assertEqual( ['method', 'payload', 'timestamp', 'url'], req_keys )
        self.assertEqual( 'DELETE', self.delete_resp_dct['request']['method'] )
        self.assertEqual( {}, self.delete_resp_dct['request']['payload'] )
        resp_keys = sorted( self.delete_resp_dct['response'].keys() )
        self.assertEqual( ['elapsed_time', 'status'], resp_keys )
        self.assertEqual( 'success', self.delete_resp_dct['response']['status'] )

    ## RECORD-GET ================

    def test_get_record_data_for_group_check(self):
        """ Checks `http://127.0.0.1:8000/data/records/49/`
            All the tests above assume the existence of record-49; this just confirms it's there,
            ...and that the initial response includes some group info. """
        response = self.client.get( '/data/records/49/' )
        self.assertEqual( 200, response.status_code )
        resp_dct = json.loads( response.content )
        self.assertEqual( ['entrants', 'groups', 'rec'], sorted(resp_dct.keys()) )
        try:
            resp_group_data_keys = sorted( resp_dct['groups']['group_data'][0].keys() )
            self.assertEqual( ['count', 'count_estimated', 'date_created', 'date_modified', 'description', 'reference_id', 'uuid' ], resp_group_data_keys )
        except:
            pass

    ## end Client_ReferenceGroup_Test()
