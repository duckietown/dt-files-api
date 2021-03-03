import os

FILES_API_PORT = 8082

DEFAULT_DATA_DIR = '/data'
DATA_DIR = os.environ.get('DATA_DIR', DEFAULT_DATA_DIR)

DEVICE_BACKUP_FILEPATH = lambda device_id, key: \
    os.path.join('device', device_id, 'backup', 'data', key.lstrip('/'))
