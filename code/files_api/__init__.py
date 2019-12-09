import os
import logging

# define logger
logging.basicConfig()
app_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
applogger = logging.getLogger(app_name)
applogger.setLevel(logging.INFO)
if 'DEBUG' in os.environ and bool(os.environ['DEBUG']):
  applogger.setLevel(logging.DEBUG)

# load app components
from .api import FilesAPI
