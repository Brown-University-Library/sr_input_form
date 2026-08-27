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


class Relationship_Test( TestCase ):
    """ Checks Record data-api urls. """

    ## DELETE =====================

    def test_delete_relationship(self):
        """ Checks good DELETE of a relationship.
            Sample api url: 'https://project_root_url/data/relationships/4671/'
                ...where `4671` is the db relationship-id
            Sample payload: {'section': 895}
                ...where `895` is the item-record-id
        """
        # self.assertEqual( 1, 2)



    ## POST =======================

    def test_post_relationship__relationship_does_not_exist(self):
        """ Checks good POST of a relationship.
            NOTE: 
            - The response to relationship-create is the same whether or not the relationship already exists.
            - The response either way is simply a redirect to the item-record.
            - If the relationship already exists, the relationship is not duplicated.
            - So these two post-tests really just allow for inspecting the logs to see the processing-flow.
            Sample api url: 'https://project_root_url/data/relationships/' (no relationship-id)
            Sample payload: {'obj': 3394, 'rel': 1, 'sbj': 2033, 'section': 895}
               ...where `3394` is a referent-id
                        `1` is an id for the drop-down relationship selected
                        `2033` is a referent-id
                        `895` is the item-record-id
            Note: some posted relationships will auto-create their inverse relationship.
                  Example: a POST of `rel': 1`, where `1` represents the relationship `enslaved by`,
                           will auto-create, for the record, the inverse-relationship that the other referent is the `owner of` (id `2`) the first referent.
                           But not all relationships do this.
                  Patrick, this is not something you have to address, but should be aware of.
        """
        ## Try to create relationship -------------------------------
        post_url = reverse( 'data_relationships_url', kwargs={'rltnshp_id': None} )
        log.debug( f'post-url, ``{post_url}``' )
        payload = {
            'sbj': 3703,
            'rel': 8,
            'obj': 3704,
            'section': 1524  # this is the item-record-id
        }
        jsn = json.dumps( payload )
        response = self.client.post( post_url, data=jsn, content_type='application/json' )
        log.debug( f'response.__dict__, ``{pprint.pformat(response.__dict__)}``' )
        log.debug( f'response.content, ``{response.content}``' )
        self.assertEqual( 302, response.status_code )
        cntnt_dct = json.loads( response.content )
        self.assertEqual( ['relationship_id', 'relationship_is_new', 'rfrnc_id'], sorted(cntnt_dct.keys()) )
        self.assertEqual( 1524, cntnt_dct['rfrnc_id'] )
        # self.assertEqual( True, cntnt_dct['relationship_is_new'] )  
        self.assertEqual( '/data/sections/1524/relationships/', response.headers['location'] )  # type: ignore
        ## Clean up: delete the relationship ------------------------

        new_relationship_id = cntnt_dct['relationship_id']
        log.debug( f'starting relationship-delete for relationship_id, ``{new_relationship_id}``' )
        delete_url = reverse( 'data_relationships_url', kwargs={'rltnshp_id': new_relationship_id, 'record_id': '1524'} )
        log.debug( f'base_delete_url, ``{delete_url}``' )
        response = self.client.delete( delete_url, data=jsn, content_type='application/json' )
        log.debug( f'response.__dict__, ``{pprint.pformat(response.__dict__)}``' )
        self.assertEqual( 302, response.status_code )
        self.assertEqual( '/data/sections/1524/relationships/', response.headers['location'] )  # type: ignore

        # new_relationship_id = cntnt_dct['relationship_id']
        # log.debug( f'starting relationship-delete for relationship_id, ``{new_relationship_id}``' )
        # base_delete_url = reverse( 'data_relationships_url', kwargs={'rltnshp_id': new_relationship_id} )
        # log.debug( f'base_delete_url, ``{base_delete_url}``' )
        # delete_url = f'{base_delete_url}?record=1524'  # this is the item-record-id
        # response = self.client.delete( delete_url, data=jsn, content_type='application/json' )
        # log.debug( f'response.__dict__, ``{pprint.pformat(response.__dict__)}``' )
        # self.assertEqual( 302, response.status_code )
        # self.assertEqual( '/data/sections/1524/relationships/', response.headers['location'] )  # type: ignore


    def test_post_relationship__relationship_already_exists(self):
        """ Checks POST of already-existing relationship.
            See "NOTE" above.
        """
        ## Try to create relationship -------------------------------
        post_url = reverse( 'data_relationships_url', kwargs={'rltnshp_id': None} )
        log.debug( f'post-url, ``{post_url}``' )
        payload = {
            'sbj': 3703,
            'rel': 7,
            'obj': 3704,
            'section': 1524  # this is the item-record-id
        }
        jsn = json.dumps( payload )
        response = self.client.post( post_url, data=jsn, content_type='application/json' )
        log.debug( f'response.__dict__, ``{pprint.pformat(response.__dict__)}``' )
        log.debug( f'response.content, ``{response.content}``' )
        self.assertEqual( 302, response.status_code )
        cntnt_dct = json.loads( response.content )
        self.assertEqual( ['relationship_id', 'relationship_is_new', 'rfrnc_id'], sorted(cntnt_dct.keys()) )
        ## removing test below because the "new" relationship_id will be different each time the test-db is uploaded with production-data.
        # self.assertEqual( b'{"rfrnc_id": 1524, "relationship_id": 12849, "relationship_is_new": false}', response.content )  # test does distinguish between bytes and str
        self.assertEqual( 1524, cntnt_dct['rfrnc_id'] )
        self.assertEqual( False, cntnt_dct['relationship_is_new'] )
        self.assertEqual( '/data/sections/1524/relationships/', response.headers['location'] )  # type: ignore


    ## GET LIST ===================

    def test_get_all_relationships__relationships_do_NOT_exist(self):
        """ Checks good GET all relationships for given item-record.
            Sample api url: 'https://project_root_url/data/sections/895/relationships/'
                ...where `895` is the item-record ID
            Sample no-relationships response (`store` is empty)...
            {'people': [{'id': 2033, 'name': 'test-first-nameB test-last-nameB'},
                        {'id': 3394, 'name': 'test-first-C test-last-C'}],
             'relationships': [{'id': 1, 'name': 'enslaved by'},
                               {'id': 2, 'name': 'owner of'},
                               {'id': 3, 'name': 'priest for'},
                               [SNIP]
                               {'id': 78, 'name': 'godchild of'},
                               {'id': 79, 'name': 'godparent of'}],
             'store': []
            }
        """
        # get_all_url = reverse( 'data_reference_relationships_url', kwargs={'rfrnc_id': '895'} )
        get_all_url = reverse( 'data_reference_relationships_url', kwargs={'rfrnc_id': '4'} )
        log.debug( f'get_all_url, ``{get_all_url}``' )
        response = self.client.get( get_all_url )
        log.debug( f'response.content, ``{response.content}``' )
        ## tests
        self.assertEqual( 200, response.status_code )
        ## main response keys
        resp_dct = json.loads( response.content )
        self.assertEqual(
            ['people', 'relationships', 'store'], sorted( resp_dct.keys() )     # these are the top-level keys in the response
            )
        ## people
        self.assertEqual(
            list, type(resp_dct['people'])                                      # 'people' is a list -- IMPORTANT: this is a list of _referents_
            )
        self.assertEqual(
            ['id', 'name'], sorted( resp_dct['people'][0].keys() )              # there will always be at least one referent, with keys of 'id' (meaning referent-id) and 'name'
            )
        ## relationships
        self.assertEqual(
            ['id', 'name'], sorted( resp_dct['relationships'][0].keys() )       # excerpt of relationships data: [{'id': 1, 'name': 'enslaved by'}, {'id': 2, 'name': 'owner of'}, {'id': 3, 'name': 'priest for'}, ...
            )
        ## store
        self.assertEqual(
            [], resp_dct['store']                                               # 'store' is where the relationship data is; it's empty when there are none
            )

    def test_get_all_relationships__relationships_DO_exist(self):
        """ Checks good GET all relationships for given item-record.
            Sample api url: 'https://project_root_url/data/sections/896/relationships/'
                ...where `896` is the item-record ID
            Note #1: only 'store' will be tested here; it's the only thing different between data-returned and no-data-returned.
            Sample 'store' response...
            'store': [{'data': {'obj': {'id': 2037, 'name': 'Zacheriah Allin'},
                                'rel': {'id': 1, 'name': 'enslaved by'},
                                'sbj': {'id': 2034, 'name': 'Canootus'}},
                       'id': 2572},
                      {'data': {'obj': {'id': 2037, 'name': 'Zacheriah Allin'},
                                'rel': {'id': 1, 'name': 'enslaved by'},
                                'sbj': {'id': 2035, 'name': 'Symon'}},
                       'id': 2574},
                      {'data': {'obj': {'id': 2037, 'name': 'Zacheriah Allin'},
                                'rel': {'id': 1, 'name': 'enslaved by'},
                                'sbj': {'id': 2036, 'name': 'Joell'}},
                       'id': 2576},
                      {'data': {'obj': {'id': 2034, 'name': 'Canootus'},
                                'rel': {'id': 2, 'name': 'owner of'},
                                'sbj': {'id': 2037, 'name': 'Zacheriah Allin'}},
                       'id': 2573},
                      {'data': {'obj': {'id': 2035, 'name': 'Symon'},
                                'rel': {'id': 2, 'name': 'owner of'},
                                'sbj': {'id': 2037, 'name': 'Zacheriah Allin'}},
                       'id': 2575},
                      {'data': {'obj': {'id': 2036, 'name': 'Joell'},
                                'rel': {'id': 2, 'name': 'owner of'},
                                'sbj': {'id': 2037, 'name': 'Zacheriah Allin'}},
                       'id': 2577}
                     ]
            Note #2: note that the latter-three linked-data-like entries are the inverse of the first-three.
                     I'm _guessing_ that only the first three were entered, and the other three were 'inferred'.
                     I'll know more when I check out the PUT results. """
        get_all_url = reverse( 'data_reference_relationships_url', kwargs={'rfrnc_id': '896'} )
        log.debug( f'get_all_url, ``{get_all_url}``' )
        response = self.client.get( get_all_url )
        log.debug( f'response.content, ``{response.content}``' )
        ## tests...
        self.assertEqual( 200, response.status_code )
        resp_dct = json.loads( response.content )
        ## main 'store' response keys
        self.assertEqual(
            ['data', 'id'], list( resp_dct['store'][0].keys() )
            )
        ## 'store/data' keys
        self.assertEqual(
            ['obj', 'rel', 'sbj'], list( resp_dct['store'][0]['data'].keys() )  # as seen above, each of these keys has for its value a dictionary with keys of 'id' and 'name'
            )

    ## end Record_Test()
