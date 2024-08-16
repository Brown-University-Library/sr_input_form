# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint, uuid
# import pytz

from django.conf import settings as project_settings
from django.contrib.auth.models import User
# from django.urls import reverse
from django.urls import reverse
from django.db import models
from django.http import HttpResponseRedirect
from django.utils import timezone

from django.db.models.signals import post_save
from django.dispatch import receiver


log = logging.getLogger(__name__)


class UserProfile( models.Model ):
    """
    - from <https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone>
    - reminder: if I know I'll need to access UserProfile entries...
      `users = User.objects.all().select_related('profile')`
      ...to minimize extra db queries.
    """
    user = models.OneToOneField( User, on_delete=models.SET_NULL, related_name='profile', null=True, blank=True )  # null=True so I can pre-create the user-profile entries if desired
    uu_id = models.UUIDField( default=uuid.uuid4, editable=False )
    email = models.EmailField( default='', blank=True )
    old_db_id = models.IntegerField( null=True, blank=True )
    can_delete_doc = models.BooleanField( default=False )
    last_logged_in = models.DateTimeField( null=True, blank=True )

    class Meta:
        managed = True

## auto create and save UserProfile entries

@receiver( post_save, sender=User )
def create_user_profile(sender, instance, created, **kwargs):
    log.debug( '\n\nstarting create_user_profile()' )
    log.debug( f'sender, ``{sender}``' )
    log.debug( f'instance, ``{pprint.pformat(instance.__dict__)}``' )
    log.debug( f'created, ``{created}``' )
    log.debug( f'kwargs, ``{kwargs}``' )
    try:  # see if there is an existing user-profile to associate -- this allows for user-profiles to be pre-created, and associated with the correct user-id when the user first logs in.
        prfl = UserProfile.objects.get( email=instance.email )
        log.debug( 'a pre-existing userprofile was found' )
        if prfl.user != instance:
            log.debug( '...but it was not linked to this user-instance' )
            prfl.user = instance
            prfl.save()
            log.debug( 'pre-existing user-profile has been matched to user' )
        else:
            log.debug( '...and it was already linked to this user-instance')
    except:
        log.exception( 'user has no matching user-profile, so one will be created (traceback follows; processing will continue)' )
        UserProfile.objects.create( user=instance )

@receiver( post_save, sender=User )
def save_user_profile(sender, instance, **kwargs):
    log.debug( '\n\nstarting save_user_profile()' )
    log.debug( f'sender, ``{sender}``' )
    log.debug( f'instance, ``{pprint.pformat(instance.__dict__)}``' )
    log.debug( f'kwargs, ``{kwargs}``' )
    instance.profile.email = instance.email  # in case preferred shib email is updated.
    # instance.profile.last_logged_in = datetime.datetime.now()
    instance.profile.last_logged_in = timezone.now()
    instance.profile.save()
    log.debug( 'looks like save worked' )

## end of UserProfile() and decorated methods


class MarkedForDeletion( models.Model ):
    """ Indicates main DB records marked for deletion, and, eventually, saves jsonized document-data. """
    id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
    old_db_id = models.IntegerField()
    doc_uu_id = models.UUIDField( default=uuid.uuid4, editable=True )
    doc_json_data = models.TextField( default="{}" )
    patron_json_data = models.TextField( default="{}" )
    create_date = models.DateTimeField( auto_now_add=True )

    def save(self, *args, **kwargs):
        try:
            json.loads( self.doc_json_data )
        except:
            message = 'problem saving entered doc_json_data'
            log.exception( f'{message}; traceback follows; processing will halt' )
            raise Exception( message )
        try:
            json.loads( self.patron_json_data )
        except:
            message = 'problem saving entered patron_json_data'
            log.exception( f'{message}; traceback follows; processing will halt' )
            raise Exception( message )
        super( MarkedForDeletion, self ).save()

    class Meta:
        managed = True
