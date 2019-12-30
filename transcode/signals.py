from mongoengine import signals
import datetime
from transcode.models import *
import logging

logger=logging.getLogger() 
logger.setLevel(logging.DEBUG)