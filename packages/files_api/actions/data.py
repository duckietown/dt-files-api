import io
import os
from pathlib import Path

from flask import Blueprint, request, send_from_directory, send_file

from files_api import logger
from files_api.archive import Zip, Tar, ArchiveError
from files_api.constants import DATA_DIR
from files_api.utils import not_found, bad_request, ok, transfer_bytes

FORMAT_TO_ARCHIVE = {
  'zip': Zip,
  'tar': Tar,
}


data = Blueprint('data', __name__)


@data.route('/data/<path:resource>', methods=['GET'])
def _data_get(resource: str):
    _format = request.args.get('format', default=None)
    # check arguments
    if _format is not None and _format not in FORMAT_TO_ARCHIVE:
        return bad_request(f"Format '{_format}' not supported")
    # get requested file from request object
    filepath = os.path.abspath(os.path.join(DATA_DIR, resource))
    filename = os.path.basename(filepath)
    logger.debug(f'Requesting: GET:[{resource}]')
    # check if the path exists
    if not os.path.exists(filepath):
        return not_found(f"Resource '{resource}' not found")
    # deliver files on match
    if _format is None and os.path.isfile(filepath):
        # send headers
        return send_from_directory(DATA_DIR, resource)
    # compress the resource
    archive = FORMAT_TO_ARCHIVE[_format]()
    if os.path.isfile(filepath):
        # compress single file
        archive.add(filepath, filename, logger)
    elif os.path.isdir(filepath):
        # compress directory
        archive.add(filepath, resource, logger)
    mime_type, _ = archive.mime()
    filename = f"{Path(filepath).stem}.{archive.extension()}"
    return send_file(archive.data(), attachment_filename=filename, mimetype=mime_type)


@data.route('/data/<path:resource>', methods=['POST'])
def _data_post(resource: str):
    _format = request.args.get('format', default=None)
    # check arguments
    if _format is not None and _format not in FORMAT_TO_ARCHIVE:
        return bad_request(f"Format '{_format}' not supported")
    # get requested file from request object
    filepath = os.path.abspath(os.path.join(DATA_DIR, resource))
    logger.debug(f'Requesting: POST:[{resource}]')
    body = io.BytesIO(request.data)
    body_len = len(request.data)
    # format is given: we need to extract an archive
    if _format is not None:
        # cannot uncompress onto a file
        if os.path.isfile(filepath):
            return bad_request(f"The path '{filepath}' points to a file")
        # extract archive
        ArchiveClass = FORMAT_TO_ARCHIVE[_format]
        archive = ArchiveClass.from_buffer(body)
        try:
            logger.debug(f"Extracting {archive.extension()} archive onto '{filepath}'...")
            archive.extract_all(filepath)
        except ArchiveError as e:
            return bad_request(e.message)
        return ok()
    # format is not given: we are working with a single file
    if os.path.isdir(filepath):
        return bad_request(f"The path '{filepath}' points to a directory")
    # dump the body into a file
    logger.debug(f"Writing a body of size {body_len}B into '{filepath}'")
    try:
        os.makedirs(Path(filepath).parent, exist_ok=True)
        with open(filepath, 'wb') as fout:
            transfer_bytes(body, fout)
    except BaseException as e:
        return bad_request(str(e))
    # ---
    return ok()
