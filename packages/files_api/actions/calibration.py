import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify

from dt_robot_utils import get_robot_name
from files_api import logger
from files_api.constants import DATA_DIR
from files_api.utils import bad_request, AppException
from .backup import _storage

calibration = Blueprint('calibration', __name__)


CALIBRATION_FPATH = lambda *args: os.path.join('config', 'calibrations', *args)
TIMEFORMAT = '%a, %d %b %Y %H:%M:%S %Z'


@calibration.route('/calibration/info/<string:calib_type>', methods=['GET'])
def _calibration_info(calib_type: str):
    robot_name = get_robot_name()
    calib_filename = f"{robot_name}.yaml"
    # ---
    source = os.path.join(DATA_DIR, CALIBRATION_FPATH(calib_type), calib_filename)
    exists = os.path.isfile(source)
    mtime = None
    if exists:
        mtime = datetime.fromtimestamp(Path(source).stat().st_mtime)
    return jsonify({
        'type': calib_type,
        'exists': os.path.isfile(source),
        'files': [
            source
        ] if exists else [],
        'time': mtime
    })


@calibration.route('/calibration/backup/perform/<string:calib_type>', methods=['GET'])
def _calibration_backup(calib_type: str):
    robot_name = get_robot_name()
    calib_filename = f"{robot_name}.yaml"
    try:
        storage, location = _storage()
    except AppException as e:
        return bad_request(e.message)
    # ---
    source = os.path.join(DATA_DIR, CALIBRATION_FPATH(calib_type), calib_filename)
    if not os.path.isfile(source):
        return jsonify({
            'type': calib_type,
            'resource': None,
            'backed-up': False
        })
    # ---
    bucket_path = location(os.path.join(CALIBRATION_FPATH(calib_type), calib_filename))
    try:
        logger.info("Uploading:", source, "->", bucket_path)
        # TODO: test this before enablying
        # storage.upload(source, bucket_path)
    except BaseException as e:
        return bad_request(str(e))
    # ---
    return jsonify({
        'type': calib_type,
        'resource': source,
        'backed-up': True
    })


@calibration.route('/calibration/backup/list/<string:calib_type>', methods=['GET'])
def _calibration_list(calib_type: str):
    try:
        storage, location = _storage()
    except AppException as e:
        return bad_request(e.message)
    # ---
    bucket_path = location(CALIBRATION_FPATH(calib_type))
    try:
        objects = storage.list_objects(bucket_path)
    except BaseException as e:
        return bad_request(str(e))
    # fetch objects' metadata
    backups = []
    for obj in objects:
        try:
            meta = storage.head(obj)
        except BaseException as e:
            logger.error(str(e))
            continue
        backups.append({
            "origin": Path(obj).stem,
            "object": obj,
            "date": meta['Last-Modified'],
            "timestamp": datetime.strptime(meta['Last-Modified'], TIMEFORMAT).timestamp(),
            "hash": meta['ETag'].replace('"', ''),
            "size": meta['Content-Length'],
            "owner": meta.get('x-amz-meta-owner-id', -1)
        })
    # sort backups by date (newest first)
    backups = sorted(backups, key=lambda b: b['timestamp'], reverse=True)
    # ---
    return jsonify({
        'type': calib_type,
        'backups': backups
    })


@calibration.route('/calibration/backup/restore/<string:calib_type>/<string:origin>',
                   methods=['GET'])
def _calibration_restore(calib_type: str, origin: str):
    robot_name = get_robot_name()
    calib_filename = f"{robot_name}.yaml"
    try:
        storage, location = _storage()
    except AppException as e:
        return bad_request(e.message)
    # ---
    bucket_path = location(CALIBRATION_FPATH(calib_type, f"{origin}.yaml"))
    destination = os.path.join(DATA_DIR, CALIBRATION_FPATH(calib_type), calib_filename)
    try:
        logger.info("Downloading:", bucket_path, "->", destination)
        storage.download(bucket_path, destination, force=True)
    except BaseException as e:
        return bad_request(str(e))
    # ---
    return jsonify({
        'type': calib_type,
        'origin': origin,
        'restored': True
    })
