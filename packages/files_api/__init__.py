import os
import logging

logging.basicConfig()
logger = logging.getLogger('FilesAPI:API')
logger.setLevel(
    logging.DEBUG if os.environ.get('DEBUG', '0').lower() in ['1', 'yes', 'true'] else logging.INFO
)
