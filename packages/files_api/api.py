import io
import os
import mimetypes
from pathlib import Path
from typing import cast, Optional

from dt_class_utils import DTProcess
from http.server import \
  ThreadingHTTPServer, \
  SimpleHTTPRequestHandler

from .archive import Zip, Tar, ArchiveError

BUFFER_SIZE_BYTES = 4 * 1024 * 1024  # 4MB
FORMAT_TO_ARCHIVE = {
  'zip': Zip,
  'tar': Tar,
}


class FilesAPI(DTProcess, ThreadingHTTPServer):

    def __init__(self, bind, data_dir):
        # move to the data dir
        os.chdir(data_dir)
        # ---
        DTProcess.__init__(self)
        ThreadingHTTPServer.__init__(self, bind, FilesAPIHTTPRequestHandler)
        # get data directory
        self.data_dir = data_dir
        # get list of excluded files
        self.exclude_paths = map(
            lambda s: s.strip(),
            (os.environ['EXCLUDE_PATHS'] if 'EXCLUDE_PATHS' in os.environ else "").split(',')
        )
        # ---
        self.logger.info(f'Ready to accept requests on {bind[0]}:{bind[1]}')

    def shutdown(self):
        ThreadingHTTPServer.shutdown(self)
        DTProcess.shutdown(self)


class FilesAPIHTTPRequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        SimpleHTTPRequestHandler.__init__(self, request, client_address, server)

    def set_headers(self, code, message, filename, content_length, mime_type='text/plain',
                    mime_enc=None):
        # open headers
        self.send_response(code, message)
        # set filename
        self.send_header('Content-Disposition', f'inline; filename="{filename}"')
        # set content length
        self.send_header('Content-Length', content_length)
        # set MIME type and encoding
        self.send_header('Content-type', mime_type)
        if mime_enc:
            self.send_header('Content-Encoding', mime_enc)
        # support CORS
        if 'Origin' in self.headers:
            self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])
        # close headers
        self.end_headers()

    def do_GET(self):
        parts = (self.path + '?').split('?')
        filepath_req, args_str = parts[0].rstrip('/'), parts[1]
        args = parse_args(args_str)
        server: FilesAPI = cast(FilesAPI, self.server)
        # check arguments
        if 'format' in args and args['format'] not in FORMAT_TO_ARCHIVE:
            return self.send_error(400, 'Bad Request', f'Format {args["format"]} not supported')
        # get requested file from request object
        filepath = os.path.join(server.data_dir, filepath_req[1:])
        filename = os.path.basename(filepath)
        server.logger.debug(f'Requesting: GET:[{filepath_req}]')
        # check if the path exists
        if not os.path.exists(filepath):
            return self.send_error(404, 'Not Found', f'Resource {filepath_req} not found')
        # use listings to deliver directories when a format is not specified
        if 'format' not in args and os.path.isdir(filepath):
            return SimpleHTTPRequestHandler.do_GET(self)
        # deliver files on match
        if 'format' not in args and os.path.isfile(filepath):
            # figure out the MIME type/enc for the requested file
            mime_type, mime_enc = mimetypes.guess_type(filepath)
            # get file size
            content_length = os.path.getsize(filepath)
            # send headers
            self.set_headers(200, 'OK', filename, content_length, mime_type, mime_enc)
            # send file
            with open(filepath, 'rb') as fin:
                transfer_bytes(fin, self.wfile)
            return
        # compress the resource
        archive = FORMAT_TO_ARCHIVE[args['format']]()
        archive.add(filepath, filepath_req, server.logger)
        mime_type, mime_enc = archive.mime()
        # return archive
        self.set_headers(
            200,
            'OK',
            f'{filename}.{archive.extension()}',
            archive.size(),
            mime_type,
            mime_enc
        )
        # send file
        transfer_bytes(archive.data(), self.wfile)

    # TODO: Use POST to receive an archive (or a plain blob) and extract/dump to disk
    def do_POST(self):
        parts = (self.path + '?').split('?')
        filepath_dest, args_str = parts[0], parts[1]
        args = parse_args(args_str)
        server: FilesAPI = cast(FilesAPI, self.server)
        filepath_dest = os.path.join(server.data_dir, filepath_dest.strip('/'))
        # validate format (if necessary)
        if 'format' in args and args['format'] not in FORMAT_TO_ARCHIVE:
            return self.send_error(400, 'Bad Request', f'Format {args["format"]} not supported')
        # format is given, we need to extract an archive
        body_len = int(self.headers['Content-Length'])
        body = io.BytesIO(self.rfile.read(body_len))
        if 'format' in args:
            ArchiveClass = FORMAT_TO_ARCHIVE[args['format']]
            archive = ArchiveClass.from_buffer(body)
            try:
                server.logger.debug(f"Extracting {archive.extension()} archive "
                                    f"onto `{filepath_dest}`...")
                archive.extract_all(filepath_dest)
            except ArchiveError as e:
                return self.send_error(400, 'Bad Request', e.message)
            return self.send_response(200, 'OK')
        # format is not given, we are working with a single file
        if os.path.isdir(filepath_dest):
            return self.send_error(400, 'Bad Request', f"The path `{filepath_dest}` "
                                                       f"points to a directory")
        # dump the body into a file
        server.logger.debug(f"Writing a body of size {body_len}B into `{filepath_dest}`")
        try:
            os.makedirs(Path(filepath_dest).parent, exist_ok=True)
            with open(filepath_dest, 'wb') as fout:
                transfer_bytes(body, fout)
        except BaseException as e:
            return self.send_error(400, 'Bad Request', str(e))
        # ---
        return self.send_response(200, 'OK')

    def send_response(self, code: int, message: Optional[str] = ...) -> None:
        super(FilesAPIHTTPRequestHandler, self).send_response(code, message)
        # this is a one-shot communication, always close at the end
        self.end_headers()

    def send_error(self, code: int, message: Optional[str] = ..., explain: Optional[str] = ...) \
            -> None:
        super(FilesAPIHTTPRequestHandler, self).send_error(code, message, explain)
        # this is a one-shot communication, always close at the end
        self.end_headers()


def parse_args(args_str):
    return {
        e.split('=')[0]: (e+'=').split('=')[1]
        for e in args_str.split('&')
    }


def transfer_bytes(bytes_in, socket_out):
    while True:
        chunk = bytes_in.read(BUFFER_SIZE_BYTES)
        if not chunk:
            break
        socket_out.write(chunk)
