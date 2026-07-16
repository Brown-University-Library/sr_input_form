# -*- coding: utf-8 -*-

""" By default, this module is not accessed.
    To use:
    - shib-protect the `/project/login/` url
    - enable the two login urls in urls.py
    - enable import and function in views.py
    - enable settings in settings_app.py """

import copy, json, logging, os, pprint

from django.contrib.auth import authenticate, get_backends, login
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from disa_app import settings_app


log = logging.getLogger(__name__)


def shib_login(func):
    """ Decorator to create a user object for the Shib user, if necessary, and log the user into Django.
        Called by views.py decorators. """
    # log.debug( 'starting shib_login() decorator' )
    def decorator(request, *args, **kwargs):
        log.debug( f'\n\n starting decorator(); coming from, ```{request.META.get("HTTP_REFERER", "referrer_unknown")}```' )
        log.debug( f'heading to, ```{request.META["PATH_INFO"]}```' )
        log.debug( f'authenticated?, ```{request.user.is_authenticated}```' )
        log.debug( f'args, ```{args}```' )
        log.debug( f'kwargs, ```{kwargs}```' )
        log.debug( f'request.path, ```{request.path}```' )
        log.debug( f'request.path_info, ```{request.path_info}```' )
        # log.debug( f'request.__dict__, ```{request.__dict__}```' )
        if request.user.is_authenticated == True:
            log.debug( 'user already logged in; skip authentication' )
            pass
        else:
            log.debug( 'user not logged in; proceed w/shib-check' )
            hlpr = LoginDecoratorHelper()
            cleaned_meta_dct = hlpr.prep_shib_dct( request.META, request.get_host() )
            user_obj = hlpr.manage_usr_obj( request, cleaned_meta_dct )
            if not user_obj:
                if request.path:
                    login_redirect_url = f'{reverse("login_url")}?next={request.path}'
                    request.session['redirect_url'] = request.path
                else:
                    login_redirect_url = reverse( 'login_url ')
                log.debug( f'no user_obj, redirecting to url, ```{login_redirect_url}```' )
                return HttpResponseRedirect( reverse('login_url') )
        return func(request, *args, **kwargs)
    return decorator


class LoginDecoratorHelper(object):
    """ Handles login decorator code. """

    def __init__( self ):
        pass

    def prep_shib_dct( self, request_meta_dct, host ):
        """ Returns dct from shib-info.
            Called by shib_login() """
        log.debug( 'starting prep_shib_dct()' )
        log.debug( f'host, ``{host}``' )
        new_dct = copy.copy( request_meta_dct )
        for (key, val) in request_meta_dct.items():  # get rid of some dictionary items not serializable
            if 'passenger' in key:
                new_dct.pop( key )
            elif 'wsgi.' in key:
                new_dct.pop( key )
        if host == '127.0.0.1' or host == '127.0.0.1:8000' or host == 'testserver' or host == 'localhost' or host == 'localhost:8000':
        # if host == '127.0.0.1' or host == '127.0.0.1:8000':
            new_dct = settings_app.TEST_META_DCT
        # log.debug( 'new_dct, ```{}```'.format(pprint.pformat(new_dct)) )
        log.debug( f'new_dct, ```{pprint.pformat(new_dct)[0:1000]}```' )
        return new_dct

    def manage_usr_obj( self, request, meta_dct ):
        """ Pull information for the Shib request and get/create and login Django User object.
            Called by shib_login() """
        ( username, netid, email ) = self.ensure_basics( meta_dct )
        if not username or not netid or not email:
            return
        usr = self.update_userobj( meta_dct )
        backend = get_backends()[0]
        usr.backend = '{module}.{classname}'.format( module=backend.__module__, classname=backend.__class__.__name__ )
        login( request, usr )  #Brute force login, see - http://djangosnippets.org/snippets/1552/
        log.debug( f'login complete; returning usr-object, ```{usr}```' )
        return usr

    def ensure_basics( self, meta_dct ):
        """ Ensures essential elements exist.
            Called by manage_usr_obj() """
        # log.debug( 'meta_dct, ```%s```' % pprint.pformat(meta_dct) )
        log.debug( f'meta_dct, ```{pprint.pformat(meta_dct)[0:1000]}```' )
        username = meta_dct.get( 'Shibboleth-eppn', None )
        netid = meta_dct.get( 'Shibboleth-brownNetId', None )
        email = meta_dct.get( 'Shibboleth-mail', None )
        # log.debug( 'username, `{usr}`; netid, `{net}`'.format( usr=username, net=netid ) )
        log.debug( f'username, `{username}`; netid, `{netid}`' )
        return ( username, netid, email )

    def update_userobj( self, meta_dct ):
        """ Grabs user object, updates and saves it.
            Called by manage_usr_obj() """
        # log.debug( 'meta_dct, ```%s```' % pprint.pformat(meta_dct) )
        log.debug( f'meta_dct, ```{pprint.pformat(meta_dct)[0:1000]}```' )
        usrnm = meta_dct['Shibboleth-eppn']
        log.debug( 'usrnm-b, `%s`' % usrnm )
        try:
            # shib_email = meta_dct.get( 'Shibboleth-mail', 'foo@foo.foo' )
            shib_email = meta_dct.get( 'Shibboleth-mail', None )
            if shib_email == None:
                shib_email = 'no_email_eppn_%s' % meta_dct['Shibboleth-eppn']
            usr, created = User.objects.get_or_create( username=usrnm, email=shib_email )
        except:
            log.exception( 'problem on get_or_create(); traceback follows; processing will continue...' )
            # raise Exception( msg )
        # netid = meta_dct['Shibboleth-brownNetId']
        # if netid in settings_app.SUPER_USERS:
        #     usr.is_superuser = True
        # if netid in settings_app.STAFF_USERS:
        #     usr.is_staff = True
        eppn = meta_dct['Shibboleth-eppn']
        if eppn in settings_app.SUPER_USERS:
            usr.is_superuser = True
        if eppn in settings_app.STAFF_USERS:
            usr.is_staff = True
        # usr.is_staff = True  # use this and comment out the lines above if, say, you define a shib-group to be able to log-in
        try:
            usr = self.update_user( usr, meta_dct )
        except Exception as e:
            msg = 'exception, ```%s```' % e
            log.debug( msg )
            # raise Exception( msg )
        try:
            usr.save()
        except Exception as e:
            msg = 'exception, ```%s```' % e
            log.debug( msg )
            # raise Exception( msg )
        log.debug( 'user updated and saved' )
        log.debug( 'user-obj, ```%s```' % pprint.pformat(usr.__dict__) )
        return usr

    def update_user( self, usr, meta_dct ):
        """ Adds user to the default group.
            Called by update_userobj() """
        usr.first_name = meta_dct.get( 'Shibboleth-givenName', '' )
        usr.last_name = meta_dct.get( 'Shibboleth-sn', '' )
        # usr.email = meta_dct['Shibboleth-mail']
        # email = meta_dct.get( 'Shibboleth-mail', None )
        # if email == None:
        #     email = 'no_email_eppn_%s' % meta_dct['Shibboleth-eppn']
        # usr.email = email
        usr.set_unusable_password()
        # usr.save()  # no need here; save happens above
        # grp = Group.objects.get( name=settings_app.STAFF_GROUP )  # group must exist; TODO: autocreate if it doesn't
        # grp.user_set.add( usr )
        log.debug( 'user updated' )
        return usr

    ## end class LoginDecoratorHelper()
