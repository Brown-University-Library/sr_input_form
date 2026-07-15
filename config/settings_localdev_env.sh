#!/bin/bash


## LOCALDEV settings for _django_ `disa_project` which are install-specific or private.
##
## This file is loaded by `env/bin/activate` when running locally...
## ...and by `project/config/passenger_wsgi.py` on our servers.
##
## When deploying on our servers, copy this file to the appropriate place, edit it, 
## ...and point to it from activate and the apache <Location> entry.


## ============================================================================
## standard project-level settings
## ============================================================================

export DISA_DJ__SECRET_KEY="example_secret_key"

export DISA_DJ__DEBUG_JSON="true"

export DISA_DJ__ADMINS_JSON='
    [
      [
        "exampleFirst exampleLast",
        "example@domain.edu"
      ]
    ]
    '

# export DISA_DJ__ALLOWED_HOSTS='["127.0.0.1", "127.0.0.1:8000", "0.0.0.0:8000", "localhost:8000"]'  # must be json
export DISA_DJ__ALLOWED_HOSTS='["0.0.0.0", "127.0.0.1", "localhost"]'  # must be json

export DISA_DJ__DATABASES_JSON='
    {
      "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "HOST": "",
        "NAME": "../DBs/dj_disa.sqlite",
        "PASSWORD": "",
        "PORT": "",
        "USER": ""
      }
    }
    '

export DISA_DJ__STATIC_URL="/static/"
export DISA_DJ__STATIC_ROOT="/static/"

export DISA_DJ__EMAIL_HOST="localhost"  
export DISA_DJ__EMAIL_PORT="1026"  # will be converted to int in settings.py
export DISA_DJ__SERVER_EMAIL="donotreply_stolen-relations-project@domain.edu"

export DISA_DJ__LOG_PATH="../logs/stolen_relations.log"
export DISA_DJ__LOG_LEVEL="DEBUG"

export DISA_DJ__CSRF_TRUSTED_ORIGINS_JSON='["localhost", "127.0.0.1"]'

## https://docs.djangoproject.com/en/1.11/topics/cache/
## - TIMEOUT is in seconds (0 means don't cache); CULL_FREQUENCY defaults to one-third
export DISA_DJ__CACHES_JSON='
{
  "default": {
    "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
    "LOCATION": "../cache_dir",
    "TIMEOUT": 0,
    "OPTIONS": {
        "MAX_ENTRIES": 1000
    }
  }
}
'


## ============================================================================
## app
## ============================================================================

export DISA_DJ__README_URL="https://github.com/Brown-University-Library/disa_dj_project/blob/main/README.md"

export DISA_DJ__MAINTENANCE_MODE_JSON="false"

####################
## browse-page
####################

export DISA_DJ__DENORMALIZED_JSON_PATH="./disa_app/static/data/denormalized.json"
export DISA_DJ__DENORMALIZED_JSON_URL="http://127.0.0.1:8000/static/data/denormalized.json"

export DISA_DJ__BROWSE_JSON_PATH="./disa_app/static/data/browse.json"
export DISA_DJ__BROWSE_JSON_URL="http://127.0.0.1:8000/static/data/browse.json"

####################
## auth
####################

export DISA_DJ__SUPER_USERS_JSON='[
]'

export DISA_DJ__STAFF_USERS_JSON='
[
  "eppn@domain.edu"
]'

export DISA_DJ__STAFF_GROUP="disa_data_editors"

export DISA_DJ__TEST_META_DCT_JSON='{
  "Shibboleth-eppn": "eppn@domain.edu",
  "Shibboleth-brownNetId": "First_Last",
  "Shibboleth-mail": "first_last@domain.edu",
  "Shibboleth-givenName": "First",
  "Shibboleth-sn": "Last"
}'

export DISA_DJ__LOGIN_PROBLEM_EMAIL="sr_problems@domain.edu"

####################
## basic auth
####################

export DISA_DJ__BROWSE_USERPASS_JSON='[
  { "example_username": "example_password" }
]'

####################
## db
####################

export DISA_DJ__DATABASE_URL="mysql+pymysql://user:user@db:3306/stolenrelations"

####################
## TEMP GROUPS (TODO - document what this is; remove if not needed)
####################

export DISA_DJ__TEMP_GROUPS_ENABLED_JSON="true"

## end ========================================================================