import os
from typing import Tuple, Callable

from dt_data_api import DataClient, Storage
from flask import Blueprint, jsonify

from dt_device_utils import get_device_id
from dt_secrets_utils import get_secret
from files_api import logger
from files_api.constants import DATA_DIR, DEVICE_BACKUP_FILEPATH
from files_api.utils import bad_request, AppException

backup = Blueprint('backup', __name__)


def _storage() -> Tuple[Storage, Callable]:
    # (try to) read the token
    try:
        token = get_secret('tokens/dt1')
    except FileNotFoundError:
        # no token? nothing to do
        msg = "No secret token 'dt1' found. Cannot use backup API endpoints."
        logger.warning(msg)
        raise AppException(msg)
    # (try to) read the device ID
    try:
        device_id = get_device_id()
    except ValueError:
        # no device ID? nothing to do
        msg = "Could not find the device's unique ID. Cannot use backup API endpoints."
        logger.warning(msg)
        raise AppException(msg)
    location = lambda key: DEVICE_BACKUP_FILEPATH(device_id, key)
    # instantiate a DCSS client pointing to the user's storage space
    client = DataClient(token=token)
    return client.storage("user"), location


@backup.route('/backup/list/<path:resource>', methods=['GET'])
def _backup_list(resource: str):
    try:
        storage, location = _storage()
    except AppException as e:
        return bad_request(e.message)
    # ---
    bucket_path = location(resource)
    try:
        files = storage.list_objects(bucket_path)
    except BaseException as e:
        return bad_request(str(e))
    # remove the '{uid}/' prefix from the files
    uid = str(storage.api.uid)
    files = list(map(lambda f: f[len(uid)+1:] if f.startswith(f"{uid}/") else f, files))
    # ---
    return jsonify({
        'resource': resource,
        'files': files
    })


@backup.route('/backup/exists/<path:resource>', methods=['GET'])
def _backup_exists(resource: str):
    try:
        storage, location = _storage()
    except AppException as e:
        return bad_request(e.message)
    # ---
    bucket_path = location(resource)
    try:
        storage.head(bucket_path)
        exists = True
    except FileNotFoundError:
        exists = False
    except BaseException as e:
        return bad_request(str(e))
    # ---
    return jsonify({
        'resource': resource,
        'exists': exists
    })


@backup.route('/backup/perform/<path:resource>', methods=['GET'])
def _backup_perform(resource: str):
    try:
        storage, location = _storage()
    except AppException as e:
        return bad_request(e.message)
    # ---
    source = os.path.join(DATA_DIR, resource)
    bucket_path = location(resource)
    try:
        storage.upload(source, bucket_path)
    except BaseException as e:
        return bad_request(str(e))
    # ---
    return jsonify({
        'resource': resource,
        'backed-up': True
    })


@backup.route('/backup/restore/<path:resource>', methods=['GET'])
def _backup_restore(resource: str):
    try:
        storage, location = _storage()
    except AppException as e:
        return bad_request(e.message)
    # ---
    bucket_path = location(resource)
    destination = os.path.join(DATA_DIR, resource)
    try:
        storage.download(bucket_path, destination, force=True)
    except BaseException as e:
        return bad_request(str(e))
    # ---
    return jsonify({
        'resource': resource,
        'restored': True
    })
