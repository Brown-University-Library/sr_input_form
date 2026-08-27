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


class Citation_Test( TestCase ):
    """ Checks citation data-api urls. """

    def setUp(self):
        self.random_new_citation_text = secrets.choice( ['aaa', 'bbb', 'ccc', 'ddd'] )  # so we can tell that stuff is really getting saved to the db
        self.random_put_citation_text = secrets.choice( ['aaa', 'bbb', 'ccc', 'ddd'] )
        self.post_resp_dct = None           # updated by create_new_citation()
        self.post_resp_id = None            # updated by create_new_citation()
        self.delete_resp_statuscode = None  # updated by delete_new_citation()
        # self.delete_resp_dct = None         # updated by delete_new_citation()
        self.delete_resp_content = None     # updated by delete_new_citation()

    ## HELPERS ====================

    def create_new_citation(self):
        """ Creates a citation for tests. """
        # post_url = reverse( 'data_documents_url', kwargs={'doc_id': None} )
        post_url = reverse( 'data_documents_url' )
        log.debug( f'post-url, ``{post_url}``' )
        payload = {
            'acknowledgements': f'acks--{self.random_new_citation_text}',
            'citation_type_id': 20,  # means the fields below will be 'Book' fields
            'comments': f'comments--{self.random_new_citation_text}',
            'fields': {
                'ISBN': '',
                'abstractNote': '',
                'accessDate': '',
                'archive': '',
                'archiveLocation': '',
                'author': '',
                'callNumber': '',
                'date': '',
                'edition': '',
                'extra': '',
                'language': '',
                'libraryCatalog': '',
                'numPages': '',
                'numberOfVolumes': '',
                'pages': '',
                'place': '',
                'publisher': '',
                'rights': '',
                'series': '',
                'seriesNumber': '',
                'shortTitle': '',
                'title': f'title--{self.random_new_citation_text}',
                'url': '',
                'volume': ''}
            }
        jsn = json.dumps( payload )
        response = self.client.post( post_url, data=jsn, content_type='application/json' )
        log.debug( f'create_new_citation response (bytes), ``{response.content}``' )
        self.assertEqual( 200, response.status_code )
        self.post_resp_dct = json.loads( response.content )  # TODO: change this to make it like delete_new_citation(); only saving response.content, and making the dict in the test.
        log.debug( f'create_new_citation response dict, ``{self.post_resp_dct}``' )
        redirect_value = self.post_resp_dct['redirect']
        parts = redirect_value.split( '/' )
        self.post_resp_id = parts[-2]
        self.assertEqual( self.post_resp_id.isnumeric(), True )

    def delete_new_citation(self):
        """ Deletes citation used by tests."""
        delete_url = reverse( 'data_documents_url', kwargs={'doc_id': self.post_resp_id} )
        response = self.client.delete( delete_url )
        self.delete_resp_statuscode = response.status_code
        self.delete_resp_content = response.content

    ## GET LIST ===================

    """ not applicable -- there _is_ code, but it is not used, for getting a list of citations """

    ## GET SINGLE ===================

    def test_get_single_bad(self):
        """ Checks bad GET of `http://127.0.0.1:8000/data/documents/foo`. """
        get_url = reverse( 'data_documents_url', kwargs={'doc_id': 'foo'} )
        log.debug( f'get_url, ``{get_url}``' )
        response = self.client.get( get_url )
        self.assertEqual( 404, response.status_code )
        self.assertEqual( b'404 / Not Found', response.content )

    def test_get_single_good(self):
        """ Checks good GET of `http://127.0.0.1:8000/data/documents/abcd/`. """
        ## create citation
        self.create_new_citation()
        ## GET
        get_url = reverse( 'data_documents_url', kwargs={'doc_id': self.post_resp_id} )
        log.debug( f'get_url, ``{get_url}``' )
        response = self.client.get( get_url )
        log.debug( f'response.content, ``{response.content}``' )
        ## tests
        self.assertEqual( 200, response.status_code )
        resp_dct = json.loads( response.content )
        self.assertEqual(
            ['doc', 'doc_types'],
            sorted(resp_dct.keys()) )
        doc_keys = sorted( resp_dct['doc'].keys() )
        self.assertEqual(
            ['acknowledgements', 'citation', 'citation_type_id', 'comments', 'fields', 'id'],
            doc_keys )
        self.assertEqual(
            f'acks--{self.random_new_citation_text}', resp_dct['doc']['acknowledgements']
            )
        self.assertEqual(
            f'title--{self.random_new_citation_text}', resp_dct['doc']['citation']
            )  # note, the display will be some combination of the `fields` data sent
        self.assertEqual(
            f'comments--{self.random_new_citation_text}', resp_dct['doc']['comments']
            )
        self.assertEqual(
            {'title': f'title--{self.random_new_citation_text}'},
            resp_dct['doc']['fields']
            )
        ## cleanup
        self.delete_new_citation()

    ## CREATE ====================

    def test_post_bad(self):
        """ Checks `http://127.0.0.1:8000/data/documents/ POST w/bad params. """
        post_url = reverse( 'data_documents_url' )
        log.debug( f'post-url, ``{post_url}``' )
        payload = {
            'foo': 'bar'
        }
        response = self.client.post( post_url, payload )
        log.debug( f'create_new_citation response (bytes), ``{response.content}``' )
        self.assertEqual( 400, response.status_code )
        self.assertEqual( b'400 / Bad Request', response.content )

    def test_post_good(self):
        """ Checks `http://127.0.0.1:8000/data/documents/ POST w/good params. """
        ## create citation
        self.create_new_citation()
        ## tests
        self.assertEqual( ['redirect'], list(self.post_resp_dct.keys()) )
        ## cleanup
        self.delete_new_citation()

    ## UPDATE ====================

    def test_put_bad(self):
        """ Checks bad PUT to `http://127.0.0.1:8000/data/documents/foo/`. """
        put_url = reverse( 'data_documents_url', kwargs={'doc_id': 'foo'} )
        put_response = self.client.put( put_url )
        self.assertEqual( 400, put_response.status_code )
        self.assertTrue( b'Bad Request' in put_response.content )

    def test_put_good(self):
        """ Checks good PUT to `http://127.0.0.1:8000/data/documents/abcd/`. """
        ## create citation
        self.create_new_citation()
        ## PUT
        put_url = reverse( 'data_documents_url', kwargs={'doc_id': self.post_resp_id} )
        log.debug( f'put_url-url, ``{put_url}``' )
        put_payload = {  # same as create, except for `shortTitle`, which was blank
            'acknowledgements': f'acks--{self.random_new_citation_text}',
            'citation_type_id': 20,  # means the fields below will be 'Book' fields
            'comments': f'comments--{self.random_new_citation_text}',
            'fields': {
                'ISBN': '',
                'abstractNote': '',
                'accessDate': '',
                'archive': '',
                'archiveLocation': '',
                'author': '',
                'callNumber': '',
                'date': '',
                'edition': '',
                'extra': '',
                'language': '',
                'libraryCatalog': '',
                'numPages': '',
                'numberOfVolumes': '',
                'pages': '',
                'place': '',
                'publisher': '',
                'rights': '',
                'series': '',
                'seriesNumber': '',
                'shortTitle': f'shortTitle--{self.random_put_citation_text}',  # <-- this is the only change
                'title': f'title--{self.random_new_citation_text}',
                'url': '',
                'volume': ''}
            }
        jsn = json.dumps( put_payload )
        put_response = self.client.put( put_url, data=jsn, content_type='application/json' )
        put_resp_dct = json.loads( put_response.content )
        log.debug( f'put_resp_dct, ``{pprint.pformat(put_resp_dct)}``' )
        ## tests
        ''' Note, they're similar the 'get' tests, with two differences:
            1) no `fields` are returned in the PUT response;
            2) the 'citation' (title) check: it now incorporates (additionally) the _updated_ `shortTitle`
        '''
        self.assertEqual( 200, put_response.status_code )
        self.assertEqual(
            ['doc', 'doc_types'],
            sorted(put_resp_dct.keys()) )
        doc_keys = sorted( put_resp_dct['doc'].keys() )
        log.debug( f'doc_keys, ``{doc_keys}``' )
        self.assertEqual( # same as `create` test
            f'acks--{self.random_new_citation_text}',
            put_resp_dct['doc']['acknowledgements']
            )
        self.assertEqual( # same as `create` test
            f'comments--{self.random_new_citation_text}',
            put_resp_dct['doc']['comments']
            )
        self.assertEqual(
            ['acknowledgements', 'citation', 'citation_type_id', 'comments', 'id'],  # no `fields`, as in the `create` response-dct
            doc_keys
            )
        self.assertEqual(
            'title--%s, shortTitle--%s' % ( self.random_new_citation_text, self.random_put_citation_text ),
            put_resp_dct['doc']['citation']
            )  # note, the display _was_ just the contents of fields['title'], but is now the contents of that, plus fields['shortTitle']
        ## cleanup
        self.delete_new_citation()




    def test_put_really_long_title_to_trigger_display_truncation(self):
        """ Checks PUT to `http://127.0.0.1:8000/data/documents/abcd/` with very long title. """
        ## create citation
        self.create_new_citation()
        ## PUT
        put_url = reverse( 'data_documents_url', kwargs={'doc_id': self.post_resp_id} )
        log.debug( f'put_url-url, ``{put_url}``' )
        very_long_title = 'This sentence is 70 characters, including the space after the period. ' * 10
        log.debug( f'very_long_title, ``{very_long_title}``' )
        put_payload = {  # same as create, except for `shortTitle`, which was blank
            'acknowledgements': '',
            'citation_type_id': 20,  # means the fields below will be 'Book' fields
            'comments': '',
            'fields': {
                'ISBN': '',
                'abstractNote': '',
                'accessDate': '',
                'archive': '',
                'archiveLocation': '',
                'author': '',
                'callNumber': '',
                'date': '',
                'edition': '',
                'extra': '',
                'language': '',
                'libraryCatalog': '',
                'numPages': '',
                'numberOfVolumes': '',
                'pages': '',
                'place': '',
                'publisher': '',
                'rights': '',
                'series': '',
                'seriesNumber': '',
                'shortTitle': '', 
                'title': f'title--{very_long_title}',
                'url': '',
                'volume': ''}
            }
        jsn = json.dumps( put_payload )
        put_response = self.client.put( put_url, data=jsn, content_type='application/json' )
        put_resp_dct = json.loads( put_response.content )
        log.debug( f'put_resp_dct, ``{pprint.pformat(put_resp_dct)}``' )
        ## tests
        self.assertEqual( 200, put_response.status_code )
        display = put_resp_dct['doc']['citation']
        log.debug( f'len(display), ``{len(display)}``' )
        self.assertEqual(
            True,
            len(display) < 500
            )
        ## cleanup
        self.delete_new_citation()







    ## DELETE ====================

    def test_delete_bad(self):
        """ Checks bad DELETE of `http://127.0.0.1:8000/data/documents/foo/`. """
        ## DELETE
        self.post_resp_id == 'foo'
        self.delete_new_citation()  # will attempt to delete citation-id `foo`
        ## tests
        self.assertEqual( 500, self.delete_resp_statuscode )
        self.assertEqual( b'500 / Server Error', self.delete_resp_content )

    def test_delete_good(self):
        """ Checks good DELETE of `http://127.0.0.1:8000/data/documents/abcd/`. """
        ## create citation
        self.create_new_citation()
        ## DELETE
        self.delete_new_citation()
        ## tests
        delete_resp_dct = json.loads( self.delete_resp_content )
        self.assertEqual( 200, self.delete_resp_statuscode )
        self.assertEqual(
            ['marked_for_deletion_result'],
            list(delete_resp_dct.keys()) )
        self.assertEqual(
            'success',
            delete_resp_dct['marked_for_deletion_result'] )

    ## end Citation_Test()
