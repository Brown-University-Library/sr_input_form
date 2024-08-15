import json, logging

from disa_app.models import UserProfile, MarkedForDeletion
from django.contrib import admin
from django.forms import ModelForm, ValidationError


log = logging.getLogger(__name__)


class MarkedForDeletionAdminForm(ModelForm):
    """ Thanks to <https://stackoverflow.com/questions/53896366/django-admin-form-validation> for the reminder of how to do this. """
    class Meta:
        model = MarkedForDeletion
        fields = '__all__'

    def clean_doc_json_data(self):
        log.debug( 'starting clean_doc_json_data()' )
        doc_json_data = self.cleaned_data['doc_json_data']
        try:
            json.loads( doc_json_data )
        except:
            message = 'problem saving entered doc_json_data'
            log.exception( f'{message}; traceback follows; processing will halt' )
            raise ValidationError('invalid doc_json_data')
        return doc_json_data

    def clean_patron_json_data(self):
        log.debug( 'starting clean_patron_json_data()' )
        patron_json_data = self.cleaned_data['patron_json_data']
        try:
            json.loads( patron_json_data )
        except:
            message = 'problem saving entered patron_json_data'
            log.exception( f'{message}; traceback follows; processing will halt' )
            raise ValidationError('invalid patron_json_data')
        return patron_json_data


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [ 'id', 'user', 'uu_id', 'email', 'old_db_id', 'last_logged_in' ]
    readonly_fields = [ 'uu_id', 'last_logged_in' ]
    search_fields = [ 'uu_id', 'email', 'old_db_id' ]


@admin.register(MarkedForDeletion)
class MarkedForDeletionAdmin(admin.ModelAdmin):
    list_display = [ 'old_db_id', 'doc_uu_id', 'doc_json_data', 'patron_json_data', 'create_date' ]
    search_fields = [ 'old_db_id', 'doc_uu_id', 'doc_json_data', 'patron_json_data' ]
    readonly_fields = [ 'create_date' ]
    form = MarkedForDeletionAdminForm


