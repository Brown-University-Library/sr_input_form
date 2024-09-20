# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from disa_app import views


admin.autodiscover()


urlpatterns = [

    ## primary app urls...

    url( r'^info/$', views.info, name='info_url' ),

    url( r'^login/$', views.login, name='login_url' ),
    url( r'^logout/$', views.logout, name='logout_url' ),
    url( r'^shib_login/$', views.handle_shib_login, name='shib_login_url' ),
    url( r'^user_pass_handler/$', views.user_pass_handler, name='user_pass_handler_url' ),

    url( r'^browse/$', views.browse_tabulator, name='browse_url' ),
    url( r'^browse_logout/$', views.browse_logout, name='browse_logout_url' ),

    # url( r'^editor/documents/$', views.edit_citation, name='edit_citation_url' ),  # no longer used; will delete
    # url( r'^editor/documents/(?P<cite_id>.*)/$', views.edit_citation, name='edit_citation_url' ),  # no longer used; will delete

    url( r'^editor/records/$', views.edit_record, name='edit_record_url' ),
    url( r'^editor/records/(?P<rec_id>.*)/$', views.edit_record_w_recid, name='edit_record_w_recid_url' ),

    url( r'^editor/person/$', views.edit_person, name='edit_person_root_url' ),
    url( r'^editor/person/(?P<rfrnt_id>.*)/$', views.edit_person, name='edit_person_url' ),
    url( r'^editor/$', views.editor_index, name='editor_index_url' ),
    url( r'^record/relationships/(?P<rec_id>.*)/$', views.edit_relationships, name='edit_relationships_url' ),

    url( r'^source/(?P<src_id>.*)/$', views.source, name='source_url' ),

    url( r'^search_results/$', views.search_results, name='search_results_url' ),

    url( r'^map/$', views.map, name='map_url' ),
    url( r'^timeline/$', views.timeline, name='timeline_url' ),

    # --------------------
    # redesign...
    # --------------------

    url( r'^redesign_home/$', views.redesign_home, name='redesign_home_url' ),
    url( r'^redesign_citations/$', views.redesign_citations, name='redesign_citations_url' ),
    url( r'^redesign_citations/(?P<cite_id>.*)/$', views.redesign_citation, name='redesign_citation_url' ),


    ## apis...

    url( r'^data/documents/$', views.data_documents, name='data_documents_url' ),
    url( r'^data/documents/(?P<doc_id>.*)/$', views.data_documents, name='data_documents_url' ),

    url( r'^data/records/$', views.data_records, name='data_record_url' ),  # note, 'refID' is passed on a PUT.
    url( r'^data/records/(?P<rec_id>.*)/$', views.data_records, name='data_record_url' ),  # note, 'refID' is passed on a PUT.
    url( r'^data/reference/(?P<rfrnc_id>.*)/$', views.data_reference, name='data_reference_url' ),

    url( r'^data/entrants/details/(?P<rfrnt_id>.*)/$', views.data_entrants_details, name='data_entrants_details_url' ),
    url( r'^data/entrants/(?P<rfrnt_id>.*)/$', views.data_entrants, name='data_referent_url' ),

    url( r'^data/sections/(?P<rfrnc_id>.*)/relationships/$', views.relationships_by_reference, name='data_reference_relationships_url' ),
    url( r'^data/relationships/$', views.data_relationships, name='data_relationships_url' ),
    # url( r'^data/relationships/(?P<rltnshp_id>.*)/$', views.data_relationships, name='data_relationships_url' ),
    url( r'^data/relationships/(?P<rltnshp_id>[^/]*)/record_(?P<record_id>.*)/$', views.data_relationships, name='data_relationships_url' ),
    url( r'^data/relationships/(?P<rltnshp_id>[^/]*)/$', views.data_relationships, name='data_relationships_url' ),

    url( r'^data/reference_group/(?P<incoming_uuid>.*)/$', views.data_reference_group, name='data_group_url' ),

    url( r'^data/$', views.data_root, name='data_root_url' ),  # a 'fake' url, for building other urls; set to return a 404 if hit directly


    ## utility-urls (protected, act as viewable integrity checks)...

    url( r'^utility/citations/$', views.utility_citations, name='utility_citations_url' ),
    # url( r'^utility/items/$', views.utility_items, name='utility_items_url' ),
    url( r'^utility/referents/$', views.utility_referents, name='utility_referents_url' ),
    # url( r'^utility/people/$', views.utility_people, name='utility_people_url' ),


    ## misc...

    url( r'^admin/', admin.site.urls ),
    url( r'^datafile/$', views.datafile, name='datafile_url' ),


    ## support urls...

    url( r'^denormalized.json$', views.dnrmlzd_jsn_prx_url, name='dnrmlzd_jsn_prx_url_url' ),  ## TODO delete
    url( r'^browse.json$', views.browse_json_proxy, name='browse_json_proxy_url' ),
    url( r'^version/$', views.version, name='version_url' ),
    url( r'^error_check/$', views.error_check, name='error_check_url' ),

    # url( r'^$', RedirectView.as_view(pattern_name='browse_url') ),
    url( r'^$', RedirectView.as_view(pattern_name='info_url') ),

    ]



# ------------------------
# routes from flask app...
# ------------------------

# @app.route('/login', methods=['GET', 'POST'])
# # def login():

# @app.route('/logout')
# # def logout():

# @app.route('/editor', methods=['GET'])
# # @login_required
# # def editor_index():

# @app.route('/editor/documents')
# @app.route('/editor/documents/<citeId>')
# # @login_required
# # def edit_citation(citeId=None):

# @app.route('/editor/records')
# @app.route('/editor/records/<recId>')
# # @login_required
# # def edit_record(recId=None):

# @app.route('/editor/person')
# @app.route('/editor/person/<entId>')
# # @login_required
# # def edit_entrant(entId=None):

# @app.route('/data/documents/', methods=['GET'])
# @app.route('/data/documents/<docId>', methods=['GET'])
# # @login_required
# # def read_document_data(docId=None):

# @app.route('/data/documents/', methods=['POST'])
# # @login_required
# # def create_citation():

# @app.route('/data/documents/', methods=['PUT'])
# @app.route('/data/documents/<citeId>', methods=['PUT'])
# # @login_required
# # def update_citation_data(citeId):

# @app.route('/data/records/', methods=['GET'])
# @app.route('/data/records/<recId>', methods=['GET'])
# # @login_required
# # def read_record_data(recId=None):

# @app.route('/data/entrants/', methods=['GET'])
# @app.route('/data/entrants/<rntId>', methods=['GET'])
# # @login_required
# # def read_referent_data(rntId=None):

# @app.route('/data/records/', methods=['POST'])
# @app.route('/data/records/<refId>', methods=['PUT'])
# # @login_required
# # def update_reference_data(refId=None):

# @app.route('/data/reference/<refId>', methods=['DELETE'])
# # def delete_reference(refId):

# @app.route('/data/entrants/', methods=['POST'])
# @app.route('/data/entrants/<rntId>', methods=['PUT', 'DELETE'])
# # @login_required
# # def update_referent(rntId=None):

# @app.route('/data/entrants/details/', methods=['PUT'])
# @app.route('/data/entrants/details/<rntId>', methods=['PUT'])
# # @login_required
# # def update_referent_details(rntId):

# @app.route('/people/')
# # def person_index():

# @app.route('/people/<persId>')
# # def get_person(persId):

# @app.route('/source/<srcId>')
# # def get_source(srcId):
# #     return redirect(url_for('edit_record', recId=srcId))

# @app.route('/record/relationships/<recId>')
# # @login_required
# # def edit_relationships(recId):

# @app.route('/data/sections/<refId>/relationships/')
# # @login_required
# # def relationships_by_reference(refId):

# @app.route('/data/relationships/', methods=['POST'])
# # @login_required
# # def create_relationship():

# @app.route('/data/relationships/<relId>', methods=['DELETE'])
# # @login_required
# # def delete_relationship(relId):

# @app.route( '/error_check' )
# # def error_check():
