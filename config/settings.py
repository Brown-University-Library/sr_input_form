"""
Django settings for disa_project.
(for app-settings, see disa_app/settings_app.py)

For more information on this file, see
<https://docs.djangoproject.com/en/3.2/topics/settings/>

For the full list of settings and their values, see
<https://docs.djangoproject.com/en/3.2/ref/settings/>
"""

import json, logging, os

log = logging.getLogger(__name__)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname( os.path.dirname(os.path.abspath(__file__)) )
# log.debug( f'BASE_DIR, ``{BASE_DIR}``' )
# BASE_DIR is the path to the project (no end-slash)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DISA_DJ__SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = json.loads( os.environ['DISA_DJ__DEBUG_JSON'] )  # will be True or False

ADMINS = json.loads( os.environ['DISA_DJ__ADMINS_JSON'] )

ALLOWED_HOSTS = json.loads( os.environ['DISA_DJ__ALLOWED_HOSTS'] )  # list


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'disa_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# template_dirs = json.loads( os.environ['DISA_DJ__TEMPLATES_JSON'] )  # if template-directory info is complex
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ '%s/disa_app/disa_app_templates' % BASE_DIR ],
        # 'DIRS': template_dirs,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.passenger_wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = json.loads( os.environ['DISA_DJ__DATABASES_JSON'] )

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'  # <https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys>cache


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'  # original setting is 'UTC'

USE_I18N = True


USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = os.environ['DISA_DJ__STATIC_URL']
STATIC_ROOT = os.environ['DISA_DJ__STATIC_ROOT']  # needed for collectstatic command


# Email
SERVER_EMAIL = os.environ['DISA_DJ__SERVER_EMAIL']
EMAIL_HOST = os.environ['DISA_DJ__EMAIL_HOST']
EMAIL_PORT = int( os.environ['DISA_DJ__EMAIL_PORT'] )


# sessions

# <https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-SESSION_SAVE_EVERY_REQUEST>
# Thinking: not that many concurrent users, and no pages where session info isn't required, so overhead is reasonable.
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


# logging

## disable module loggers
# existing_logger_names = logging.getLogger().manager.loggerDict.keys()
# print '- EXISTING_LOGGER_NAMES, `%s`' % existing_logger_names
logging.getLogger('requests').setLevel( logging.WARNING )

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.FileHandler',  # note: configure server to use system's log-rotate to avoid permissions issues
            'filename': os.environ.get(u'DISA_DJ__LOG_PATH'),
            'formatter': 'standard',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
            },
        'disa_app': {
            # 'handlers': ['logfile', 'console'],  # leaving here as reminder that this is how to show output in the terminal
            'handlers': ['logfile', 'console'],
            'level': os.environ.get(u'DISA_DJ__LOG_LEVEL'),
            'propagate': False
        },
    }
}


## https://docs.djangoproject.com/en/1.11/topics/cache/
CACHES = json.loads( os.environ['DISA_DJ__CACHES_JSON'] )
