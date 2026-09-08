"""
Adds a uuid to each referent entry that doesn't have one.
- find referents without a uuid.
- for each...
    - add uuid

Usage:
- cd to project dir
- $ uv run ./disa_app/lib/one_off_add_referent_uuids.py
"""

import logging, os, pprint, sys, uuid

import django, sqlalchemy
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session as alch_session  # just for type-checking

## configure django paths
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
cwd = os.getcwd()  # assumes the cwd is the project directory
if cwd not in sys.path:
    sys.path.append( cwd )
django.setup()

## ok, now django-related imports will work
from disa_app import models_sqlalchemy as models_alch
from disa_app import settings_app


## set up file logger
LOG_PATH = os.environ['DISA_DJ__LOG_PATH']
LOG_LEVEL = os.environ['DISA_DJ__LOG_LEVEL']
level_dct = { 'DEBUG': logging.DEBUG, 'INFO': logging.INFO }
logging.basicConfig(
    filename=LOG_PATH, level=level_dct[LOG_LEVEL],
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s', datefmt='%d/%b/%Y %H:%M:%S' )
log = logging.getLogger(__name__)
log.info( '\n\ngenerate-browse-data log ready' )


def manage_add_uuids() -> None:
    """ Manager for adding uuids.
        Called by if name == main... """
    log.debug( 'starting manage_add_uuids()' )
    session = make_session()
    ## count all referents ------------------------------------------
    referents_all = session.query( models_alch.Referent ).all()
    log.debug( f'referents_all count, ``{len(referents_all)}``' )
    ## get relevant referents ---------------------------------------
    qset_rfrnts = session.query( models_alch.Referent ).filter(
        or_(
            models_alch.Referent.uuid == None
            ) ).all()
    log.debug( f'empty referents count, ``{len(qset_rfrnts)}``' )
    log.debug( f'Referents, ``{pprint.pformat(qset_rfrnts)}``' )
    ## update each --------------------------------------------------
    for rfrnt in qset_rfrnts:
        rfrnt.uuid = uuid.uuid4().hex    
        session.add( rfrnt )
        session.commit()
    return
        

def make_session() -> alch_session:
    """ Sets up sqlalchemy session.
        Called by manage_add_uuids() controller. """
    engine = create_engine( settings_app.DB_URL, echo=False )
    Session = sessionmaker( bind=engine )
    session = Session()
    return session




if __name__ == '__main__':
    manage_add_uuids()