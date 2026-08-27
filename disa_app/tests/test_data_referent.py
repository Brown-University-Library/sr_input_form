# -*- coding: utf-8 -*-

import json, logging, pprint, random, secrets, uuid
from operator import itemgetter

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


class Client_Referent_API_Test( TestCase ):
    """ Checks `/entrant/1234/` api urls. """

    def setUp(self):
        self.new_db_id = None
        self.post_resp_dct = {}
        self.delete_resp_dct = {}
        log.debug( f'initial self.new_db_id, ``{self.new_db_id}``' )
        log.debug( f'self.post_resp_dct, ``{self.post_resp_dct}``' )
        log.debug( f'self.delete_resp_dct, ``{self.delete_resp_dct}``' )

    # ## HELPERS ====================

    def create_new_referent(self):
        """ Creates a referent for tests. """
        post_url = reverse( 'data_referent_url', kwargs={'rfrnt_id': 'new'} )
        log.debug( f'post-url, ``{post_url}``' )
        payload = {
            'id': 'new',
            'name': {'first': 'test-first-1044', 'id': 'name', 'last': 'test-last-1044'},
            'record_id': '49',
            'roles': [
                {'id': '3', 'name': 'Priest'},
                {'id': '30', 'name': 'Previous Owner'}
            ]
        }
        jsn = json.dumps( payload )
        response = self.client.post( post_url, data=jsn, content_type='application/json' )
        self.assertEqual( 200, response.status_code )
        self.post_resp_dct: dict = json.loads( response.content )  # type: ignore
        log.debug( f'post_resp_dct, ``{pprint.pformat(self.post_resp_dct)}``' )
        self.new_db_id = self.post_resp_dct['id']
        self.assertEqual( type(self.new_db_id), int )
        log.debug( f'self.new_db_id, ``{self.new_db_id}``' )
        self.assertEqual( str, type(self.post_resp_dct["uuid"]) )

    def delete_new_referent(self):
        """ Deletes referent used by tests."""
        delete_url = reverse( 'data_referent_url', kwargs={'rfrnt_id': self.new_db_id} )
        response = self.client.delete( delete_url )
        self.assertEqual( 200, response.status_code )
        self.delete_resp_dct: dict = json.loads( response.content )  # type: ignore
        log.debug( f'delete_resp_dct, ``{pprint.pformat(self.delete_resp_dct)}``' )

    ## GET =======================

    def test_get_bad(self):
        """ Checks bad GET of `http://127.0.0.1:8000/data/entrants/foo/`. """
        get_url = reverse( 'data_referent_url', kwargs={'rfrnt_id': 'foo'} )
        log.debug( f'get_url, ``{get_url}``' )
        response = self.client.get( get_url )
        self.assertEqual( 404, response.status_code )
        self.assertTrue( b'Not Found' in response.content )  # type: ignore

    def test_get_good(self):
        """ Checks good GET of `http://127.0.0.1:8000/data/entrants/1234/`. """
        ## create referent
        self.create_new_referent()
        log.debug( f'new_db_id, ``{self.new_db_id}``' )
        ## GET
        get_url = reverse( 'data_referent_url', kwargs={'rfrnt_id': self.new_db_id} )
        log.debug( f'get_url, ``{get_url}``' )
        response = self.client.get( get_url )
        ## tests
        self.assertEqual( 200, response.status_code )
        resp_dct: dict = json.loads( response.content )  # type: ignore
        self.assertEqual( ['ent'], sorted(resp_dct.keys()) )
        rfrnt_data_keys = sorted( resp_dct['ent'].keys() )
        # self.assertEqual( ['method', 'payload', 'timestamp', 'url'], req_keys )
        self.assertEqual(
            ['age_category', 'age_number', 'age_text', 'enslavements', 'id', 'names', 'occupation_text', 'origins', 'races', 'sex', 'titles', 'tribes', 'uuid', 'vocations'],
            rfrnt_data_keys
            )
        ## cleanup
        self.delete_new_referent()

    ## CREATE ====================

    def test_post_bad(self):
        """ Checks POST to `http://127.0.0.1:8000/data/entrants/abcd/ w/bad params. """
        post_url = reverse( 'data_referent_url', kwargs={'rfrnt_id': 'new'} )
        log.debug( f'post-url, ``{post_url}``' )
        payload = {
            'foo': 'bar'
        }
        jsn = json.dumps( payload )
        response = self.client.post( post_url, data=jsn, content_type='application/json' )
        self.assertEqual( 400, response.status_code )
        self.assertTrue( b'Bad Request' in response.content )  # type: ignore

    def test_post_good(self):
        """ Checks POST to `http://127.0.0.1:8000/data/entrants/1234/` w/good params. """
        ## create referent
        self.create_new_referent()
        ## tests
        self.assertEqual( 
            ['first', 'id', 'last', 'name_id', 'person_id', 'roles', 'uuid'], 
            sorted(self.post_resp_dct.keys()) )
        ## cleanup
        self.delete_new_referent()

    ## UPDATE ====================

    ## NOTE: referent PUTs are handled by a different endpoint; see the Client_Referent_Details_API_Test() class below.

    # def test_put_bad(self):
    #     """ Checks bad PUT to `http://127.0.0.1:8000/data/entrants/1234/` -- no payload. """
    #     put_url = reverse( 'data_referent_url', kwargs={'rfrnt_id': 'foo'} )
    #     put_response = self.client.put( put_url )  # will fail; no payload
    #     self.assertEqual( 400, put_response.status_code )
    #     self.assertTrue( b'Bad Request' in put_response.content )  # type: ignore

    # def test_put_good(self):
    #     """ Checks good PUT to `http://127.0.0.1:8000/data/entrants/1234/`. """
    #     ## create referent
    #     self.create_new_referent()
    #     ## PUT
    #     put_url = reverse( 'data_referent_url', kwargs={'rfrnt_id': self.new_db_id} )
    #     log.debug( f'put_url-url, ``{put_url}``' )
    #     random_name_part = secrets.choice( ['nameA', 'nameB', 'nameC', 'nameD'] )
    #     put_payload = {
    #         'id': self.new_db_id,
    #         'name': {'first': f'test-first-{random_name_part}', 'id': 'name', 'last': f'test-last-{random_name_part}'},
    #         'record_id': '49',
    #         'roles': [
    #             {'id': '3', 'name': 'Priest'},
    #             {'id': '30', 'name': 'Previous Owner'}
    #         ]
    #     }
    #     jsn = json.dumps( put_payload )
    #     put_response = self.client.put( put_url, data=jsn, content_type='application/json' )
    #     ## tests
    #     self.assertEqual( 200, put_response.status_code )
    #     resp_dct: dict = json.loads( put_response.content )  # type: ignore
    #     self.assertEqual( 
    #         ['first', 'id', 'last', 'name_id', 'person_id', 'roles', 'uuid'], 
    #         sorted(resp_dct.keys()) )
    #     self.assertEqual( f'test-first-{random_name_part}', resp_dct['first'] )
    #     self.assertEqual( f'test-last-{random_name_part}', resp_dct['last'] )
    #     ## cleanup
    #     self.delete_new_referent()

    ## DELETE ====================

    def test_delete_bad(self):
        """ Checks bad DELETE of `http://127.0.0.1:8000/data/entrants/foo/`. """
        delete_url = reverse( 'data_referent_url', kwargs={'rfrnt_id': 'foo'} )
        delete_response = self.client.delete( delete_url )
        self.assertEqual( 500, delete_response.status_code )
        self.assertTrue( b'Server Error' in delete_response.content )  # type: ignore

    def test_delete_good(self):
        """ Checks good DELETE of `http://127.0.0.1:8000/data/entrants/1234/`. """
        ## create referent
        self.create_new_referent()
        ## DELETE
        self.delete_new_referent()
        ## tests
        self.assertEqual( ['id'], sorted(self.delete_resp_dct.keys()) )

    ## end Client_Referent_API_Test()


class Client_Referent_Details_API_Test( TestCase ):
    """ Checks `/entrant/details/1234/` api urls. """

    ## UPDATE-DETAILS ============ (separate view)

    # def test_put_details_bad(self):
    #     """ Checks bad PUT to `http://127.0.0.1:8000/data/entrants/details/1234/` -- no payload. """
    #     put_url = reverse( 'data_entrants_details_url', kwargs={'rfrnt_id': 'foo'} )
    #     put_response = self.client.put( put_url )  # will fail; no payload
    #     self.assertEqual( 400, put_response.status_code )
    #     self.assertTrue( b'Bad Request' in put_response.content )

    def test_put_details_good(self):
        """ Checks good PUT to `http://127.0.0.1:8000/data/entrants/details/1234/`.
            Note: the `random` part is to ensure there is different data being sent, and checked. 
            
            [18/Jan/2024 15:46:21] DEBUG [view_data_entrant_manager-execute_details_update()::190] submitted data, ``{'id': '4110', 'record_id': '1676', 'age': 'some other age-text', 'age_text': 'some other age-text', 'age_number': 13.5, 'age_category': '3a592293-9d21-4cef-968a-fcebfd1c0835', 'names': [{'first': 'Henry', 'id': '4122', 'last': 'Huggins', 'name_type': '8'}], 'origins': [], 'races': [], 'roles': [], 'sex': 'Male', 'statuses': [], 'titles': [], 'tribes': [], 'vocations': []}``

            """
        ## create referent
        # self.test_put_details_good_new_referent() -- eventually
        ## PUT
        target_rfrnt_id = '2033'
        put_details_url = reverse( 'data_entrants_details_url', kwargs={'rfrnt_id': target_rfrnt_id} )
        log.debug( f'put_details_url, ``{put_details_url}``' )
        random_name_part = secrets.choice( ['nameA', 'nameB', 'nameC'] )
        random_race_partA = secrets.choice( ['Indian', 'Indio'] )
        random_race_partB = secrets.choice( ['White', 'Unknown'] )
        random_tribe_partA = secrets.choice( ['Bocotora', 'Eastern Pequot'] )
        random_tribe_partB = secrets.choice( ['Mohegan', 'Wampanoag'] )
        occupation_text = 'a job description ' + str(random.uniform(1, 20))

        ## create a random float with one decimal point
        random_age_number = round(random.uniform(1, 20), 1)
        random_age_text = str( random_age_number )
        random_uuid = secrets.choice( [
            '78ac411b-be39-41e3-be66-43017e30d105', 
            '761cc55d-8bf6-4737-a728-30f20c4d66b2',
            '3a592293-9d21-4cef-968a-fcebfd1c0835',
            ] )

        put_details_payload = {
            'names': [ {'id': target_rfrnt_id, 'first': f'test-first-{random_name_part}', 'last': f'test-last-{random_name_part}', 'name_type': '7'} ],
            'age_text': random_age_text,
            'age_number': random_age_number,
            'age_category': random_uuid,
            'sex': 'Other',
            # 'races': [ {'id': 'India', 'name': 'India'}, {'id': 'Mustee', 'name': 'Mustee'} ],
            'races': [ {'id': random_race_partA, 'name': random_race_partA}, {'id': random_race_partB, 'name': random_race_partB} ],
            # 'tribes': [ {'id': 'Bocotora', 'name': 'Bocotora'}, {'id': 'Eastern Pequot', 'name': 'Eastern Pequot'} ],
            'tribes': [ {'id': random_tribe_partA, 'name': random_tribe_partA}, {'id': random_tribe_partB, 'name': random_tribe_partB} ],
            'origins': [],
            'statuses': [],
            'titles': [],
            'vocations': [],
            'occupation_text': occupation_text
        }
        jsn = json.dumps( put_details_payload )
        put_details_response = self.client.put( put_details_url, data=jsn, content_type='application/json' )
        put_details_resp_dct: dict = json.loads( put_details_response.content )  # type: ignore -- should be, i.e., `{'redirect': '/editor/records/895/'}`
        log.debug( f'put_details_resp_dct, ``{pprint.pformat(put_details_resp_dct)}``' )
        ## tests -- response
        self.assertEqual( 200, put_details_response.status_code )
        ( key, val ) = list( put_details_resp_dct.items() )[0]
        self.assertEqual( 'redirect', key )
        self.assertTrue( '/editor/records/' in val )
        ## tests -- get and compare
        get_url = reverse( 'data_referent_url', kwargs={'rfrnt_id': 2033} )
        log.debug( f'get_url for details comparison, ``{get_url}``' )
        get_response = self.client.get( get_url )
        get_resp_dct: dict = json.loads( get_response.content )  # type: ignore
        log.debug( f'get_resp_dct, ``{pprint.pformat(get_resp_dct)}``' )
        self.assertEqual(
            [{'first': f'test-first-{random_name_part}', 'id': 2033, 'last': f'test-last-{random_name_part}', 'name_type': 'Given'}],
            get_resp_dct['ent']['names'],
            )
        self.assertEqual(
            [{'id': random_race_partA, 'label': random_race_partA, 'value': random_race_partA}, {'id': random_race_partB, 'label': random_race_partB, 'value': random_race_partB}],
            # get_resp_dct['ent']['races'],
            sorted( get_resp_dct['ent']['races'], key=itemgetter('label') ),  ## sort needed because sometimes the data is returned in a different sort-order
            )
        self.assertEqual(
            [{'id': random_tribe_partA, 'label': random_tribe_partA, 'value': random_tribe_partA}, {'id': random_tribe_partB, 'label': random_tribe_partB, 'value': random_tribe_partB}],
            # get_resp_dct['ent']['tribes'],
            sorted( get_resp_dct['ent']['tribes'], key=itemgetter('label') ),
            )
        ## test age
        self.assertEqual( random_age_text, get_resp_dct['ent']['age_text'] )
        self.assertEqual( random_age_number, get_resp_dct['ent']['age_number'] )
        self.assertEqual( random_uuid, get_resp_dct['ent']['age_category'] )
        ## test occupation
        self.assertEqual( occupation_text, get_resp_dct['ent']['occupation_text'] )
        ## cleanup
        # self.delete_new_referent() -- eventually

    ## end Client_Referent_Details_API_Test()
