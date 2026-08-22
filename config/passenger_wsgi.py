# -*- coding: utf-8 -*-

"""
WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

"""
Passenger selects the uv-created environment through its Python configuration.
Application settings are loaded from the outer `.env` by `config.settings`.
"""

## silence sqlalchemy logging
"""
This is one of the earliest files loaded, so it's a good place to silence the sqlalchemy logging.
"""
import logging
logging.getLogger('sqlalchemy.engine.base.Engine').setLevel( logging.WARNING )
logging.getLogger('sqlalchemy.engine.base').setLevel( logging.WARNING )
logging.getLogger('sqlalchemy.engine').setLevel( logging.WARNING )


import os, sys
from django.core.wsgi import get_wsgi_application


PROJECT_DIR_PATH = os.path.dirname( os.path.dirname(os.path.abspath(__file__)) )

## update path
sys.path.append( PROJECT_DIR_PATH )

## reference django settings
os.environ[u'DJANGO_SETTINGS_MODULE'] = 'config.settings'  # so django can access its settings

## gogogo
application = get_wsgi_application()
