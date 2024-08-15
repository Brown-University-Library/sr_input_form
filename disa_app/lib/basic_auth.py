import base64, logging
from disa_app import settings_app
from django.http import HttpResponse


log = logging.getLogger(__name__)


class BasicAuthHelper( object ):

    def check_basic_auth( self, request ):
        """ Checks for any, and correct, http-basic-auth info, returns boolean.
            Called by views.try_again() """
        # ( GOOD_USER, GOOD_PASSWORD ) = ( unicode(os.environ['EZSCAN__BASIC_AUTH_USERNAME']), unicode(os.environ['EZSCAN__BASIC_AUTH_PASSWORD']) )
        basic_auth_ok = False
        auth_info = request.headers.get( 'authorization', None )
        if ( auth_info and auth_info.startswith('Basic ') ):
            basic_info = auth_info.lstrip( 'Basic ' )
            decoded_basic_bytes = base64.b64decode( basic_info )
            log.debug( 'type(decoded_basic_bytes), `%s`; decoded_basic_bytes, ```%s```' % (type(decoded_basic_bytes), decoded_basic_bytes) )
            decoded_basic_str = decoded_basic_bytes.decode( 'utf-8' )
            ( received_username, received_password ) = decoded_basic_str.rsplit( ':', 1 )   # cool; 'rsplit-1' solves problem if 'username' contains one or more colons
            log.debug( f'received_username, ``{received_username}``; received_password, ``{received_password}``' )
            # for ( good_username, good_password ) in user_pass.items()[0] in settings_app.BASIC_AUTH_LIST:
            for user_pass in settings_app.BASIC_AUTH_LIST:
                ( good_username, good_password ) = list( user_pass.items() )[0]
                log.debug( f'good_username, ``{good_username}``; good_password, ``{good_password}``' )
                if received_username == good_username and received_password == good_password:
                    basic_auth_ok = True
                    break
        log.debug( f'basic_auth_ok, ``{basic_auth_ok}``' )
        return basic_auth_ok

    def display_prompt( self ):
        """ Builds http-basic-auth response which brings up username/password dialog box.
            Called by views.try_again() """
        response = HttpResponse()
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="DISA_data-entry-form"'
        return response

    # end class BasicAuthHelper






# from illiad3-web-app...

# import base64, logging, pprint
# from illiad_app import settings_app


# log = logging.getLogger(__name__)


# def check_basic_auth( request ):
#     """ Checks for any, and correct, http-basic-auth info, returns boolean.
#         Called by views.try_again() """
#     log.debug( 'request.__dict__, ```%s```' % pprint.pformat(request.__dict__) )
#     basic_auth_ok = False
#     auth_info = request.META.get( 'HTTP_AUTHORIZATION', None )
#     log.debug( 'type(auth_info), `%s`; auth_info, ```%s```' % (type(auth_info), auth_info) )
#     if ( auth_info and auth_info.startswith('Basic ') ):
#         basic_info = auth_info.lstrip( 'Basic ' )
#         decoded_basic_bytes = base64.b64decode( basic_info )
#         log.debug( 'type(decoded_basic_bytes), `%s`; decoded_basic_bytes, ```%s```' % (type(decoded_basic_bytes), decoded_basic_bytes) )
#         decoded_basic_str = decoded_basic_bytes.decode( 'utf-8' )
#         ( received_username, received_password ) = decoded_basic_str.rsplit( ':', 1 )   # cool; 'rsplit-1' solves problem if 'username' contains one or more colons
#         log.debug( 'received_username, ```%s```; received_password, ```%s`' % (received_username, received_password) )
#         if received_username == settings_app.BASIC_AUTH_USER and received_password == settings_app.BASIC_AUTH_PASSWORD:
#             basic_auth_ok = True
#     log.debug( 'basic_auth_ok, `%s`' % basic_auth_ok )
#     return basic_auth_ok


base64
