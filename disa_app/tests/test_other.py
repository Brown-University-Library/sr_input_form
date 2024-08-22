# -*- coding: utf-8 -*-

import json, logging, pathlib, pprint, uuid

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


class Browse_Test( TestCase ):
    """ Checks /browse/ responses. """

    def test_json_response__logged_in_false(self):
        """ Checks ?format=json param. """
        response = self.client.get( '/browse/?format=json' )
        self.assertEqual( 200, response.status_code )
        resp_dct = json.loads( response.content )
        returned_keys = list( resp_dct.keys() )
        expected_keys = [ 'LOGIN_PROBLEM_EMAIL', 'browse_login_password', 'browse_login_username', 'contact_url' ]
        self.assertEqual( expected_keys.sort(), returned_keys.sort() )


class Client_Misc_Test( TestCase ):
    """ Checks miscellaneous url responses. """

    def test_browse_url(self):
        """ Checks '/browse/'. """
        response = self.client.get( '/browse/' )  # project root part of url is assumed
        self.assertEqual( 200, response.status_code )  # login landing page
        self.assertEqual( True, b'login' in response.content )

    def test_root_url_no_slash(self):
        """ Checks '/root_url' (with no slash). """
        response = self.client.get( '' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )  # permanent redirect
        # redirect_url = response._headers['location'][1]
        redirect_url = response.headers['location']  # type: ignore
        self.assertEqual(  '/info/', redirect_url )

    def test_root_url_slash(self):
        """ Checks '/root_url/' (with slash). """
        response = self.client.get( '/' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )  # permanent redirect
        # redirect_url = response._headers['location'][1]
        # log.debug( f'response, ``{response}``' )
        # log.debug( f'response.__dict__, ``{pprint.pformat(response.__dict__)}``' )
        redirect_url = response.headers['location']  # type: ignore
        self.assertEqual(  '/info/', redirect_url )

    @override_settings(DEBUG=True)
    def test_error_url_on_dev(self):
        """ Checks that '/error_check/' url generates an exception in development.
            Note: for tests, django sets settings.DEBUG to False, thus this override.
            Note: for tests, django will not trigger the email, so setting another terminal window to:
                  python3 -m smtpd -n -c DebuggingServer localhost:1026
                  ...will not show a sent email (it will on a localhost web-hit of the url, though)
            Thanks to B.C. and <https://stackoverflow.com/a/13596201> for figuring out how to test for an exception. """
        log.debug( f'project_settings.DEBUG, ``{project_settings.DEBUG}``' )
        result = 'init'
        try:
            response = self.client.get( '/error_check/' )
        except Exception as e:
            log.debug( f'e, ``{e}``' )
            result = repr(e)
        self.assertTrue( 'Exception' in result )  # web-hit returns standard 500 http-status
        self.assertTrue( 'error-check triggered; admin emailed' in result )

    def test_error_url_on_production(self):
        """ Checks '/error_check/' url.
            Note: for testing, django defaults settings.DEBUG to False """
        log.debug( f'project_settings.DEBUG, ``{project_settings.DEBUG}``' )
        response = self.client.get( '/error_check/' )
        self.assertEqual( 404, response.status_code )

    @override_settings(DEBUG=True)  # necessary because settings default to False, resulting in a 200/'Not yet running on production.' response.
    def test_redesign_citation(self):
        """ Checks '/redesign_citations/992/' -- i.e., a specific citation. """
        response = self.client.get( '/redesign_citations/992/' )
        log.debug( f'response.status_code, ``{response.status_code}``' )
        log.debug( f'response.content, ``{response.content}``' )
        self.assertEqual( 200, response.status_code )

    # end class Client_Misc_Test()


class ClientDocDataTest( TestCase ):
    """ Checks document-data url responses. """

    ## does not pass -- 2023-Feb-16 this may be worth keeping and getting running. ##
    # def test_doc_get_not_logged_in(self):
    #     """ Checks GET. """
    #     response = self.client.get( '/data/documents/1/' )
    #     log.debug( f'response, ``{response}``' )
    #     log.debug( f'response.__dict__, ``{response.__dict__}``' )
    #     self.assertEqual( 302, response.status_code )  # permanent redirect
    #     redirect_url = response._headers['location'][1]
    #     self.assertEqual(  '/login/', redirect_url )

    def test_data_doc_get_logged_in(self):
        """ Checks that logged-in api-GET returns response. """
        usr = User.objects.create( username='test_user' )
        usr.set_password('test_password')
        usr.save()  # creates a UserProfile object
        client = Client()
        logged_in = client.login( username='test_user', password='test_password' )
        self.assertEqual( True, logged_in )  # but does not get past shib-decorator -- request.user.is_authenticated stays False; added host-check to shib-decorator
        response = self.client.get( '/data/documents/1/' )
        log.debug( f'response, ``{response}``' )
        log.debug( f'response.__dict__, ``{response.__dict__}``' )
        self.assertEqual( 200, response.status_code )  # not yet working -- should be 200, but redirects to login

    # def test_good_doc_get_logged_in(self):  # no longer needed; will delete
    #     """ Checks that logged-in docoumet-GET, for existing citation, returns response. """
    #     usr = User.objects.create( username='test_user' )
    #     usr.save()  # creates a UserProfile object
    #     client = Client()
    #     client.force_login( usr )  # does not get past shib-decorator -- request.user.is_authenticated stays False; added host-check to shib-decorator
    #     response = self.client.get( '/editor/documents/1/' )
    #     self.assertEqual( 200, response.status_code )
    #     self.assertTrue( b'Document...' in response.content )

    def test_not_found_doc_get_logged_in(self):
        """ Checks that logged-in docoumet-GET, for non-existent citation, returns 404. """
        usr = User.objects.create( username='test_user' )
        usr.save()  # creates a UserProfile object
        client = Client()
        client.force_login( usr )  # does not get past shib-decorator -- request.user.is_authenticated stays False; added host-check to shib-decorator
        response = self.client.get( '/editor/documents/99999/' )
        self.assertEqual( 404, response.status_code )


class SearchTest( TestCase ):
    """ Checks `view_search_results_manager` module. """

    def test_transcription_excerpt(self):
        """ Checks transcription-excertp prep for multiple cases. """
        source = """Details of advertisement: \"Ran away from Capt. John A of Boston, on Monday the 12th Currant, a tall lusty Indian Man call'd Harry, about 19 Years of Age, with a black Hat, brown Ozenbridge Breeches and Jacket: Whoever will take up said India, and bring or convey him safe either to John C Post master of Boston, or to Mr. Nathaniel N of Kingstown in Naraganset, Master to said Indian, shall have a sufficient Reward.\""""
        tests = [
            {
                'title': 'lowercase',
                'search': 'john',
                'expected': [
                    '…of advertisement: "Ran away from Capt. John A of Boston, on Monday the 12th Currant…',
                    '…and bring or convey him safe either to John C Post master of Boston, or to Mr. Nath…']
            }, {
                'title': 'uppercase',
                'search': 'John',
                'expected': [
                    '…of advertisement: "Ran away from Capt. John A of Boston, on Monday the 12th Currant…',
                    '…and bring or convey him safe either to John C Post master of Boston, or to Mr. Nath…']
            }, {
                'title': 'beginning',
                'search': 'detail',
                'expected': ['…Details of advertisement: "Ran away from Capt.…']
            }, {
                'title': 'near_end',
                'search': 'reward',
                'expected': ['…to said Indian, shall have a sufficient Reward."…']
            }, {
                'title': 'blank',
                'search': 'foo',
                'expected': []
            }
        ]
        for test in tests:
            ( title, search, expected ) = ( test['title'], test['search'], test['expected'] )
            # self.assertSequenceEqual(
            excerpt = view_search_results_manager.update_transcription( source, search )
            self.assertEqual(
                expected,
                excerpt,
                f'error on search-title, ``{title}``; excerpt, ```{excerpt}```'
                )

    # end class SearchTest()


class DockerTest( TestCase ):
    """ Checks Docker stuff. """

    def test_requirements_exists(self):
        """ Checks that the requirements file specified in the Dockerfile(s) actually exists. 
            Note that there's no `break` after a successful assert, 
                because there can be more than one requirements-line in a Dockerfile. """
        ## get dockerfile paths -------------------------------------
        dockerfile_paths: list = [ './Dockerfile', './Dockerfile.dev' ]
        for dockerfile_path in dockerfile_paths:
            dockerfile_lines = []
            with open( dockerfile_path ) as f:
                dockerfile_lines = f.readlines()
            for line in dockerfile_lines:
                if 'requirements' in line:
                    ## get requirements filename --------------------
                    req_filestem_start_idx = line.find( 'requirements' )
                    suffix = '.txt'
                    req_filestem_end_idx = line.find( suffix, req_filestem_start_idx )  # looks for `.txt` _after_ `requirements` 
                    req_filestem = line[ req_filestem_start_idx:req_filestem_end_idx ].strip()  # would find, say, `requirements` or `requirements_local`
                    req_filename = f'{req_filestem}{suffix}'
                    req_filepath_to_test = pathlib.Path( f'./config/{req_filename}' ).resolve()
                    ## assertion ------------------------------------
                    failure_message = f'in dockerfile, ``{dockerfile_path}``, the requirements, ``{req_filepath_to_test}`` does not exist'
                    self.assertTrue( req_filepath_to_test.exists(), failure_message )
                    log.debug( 'test passed' )
                        