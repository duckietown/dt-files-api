import os
import mimetypes
from dt_class_utils import DTProcess
from http.server import \
  ThreadingHTTPServer, \
  BaseHTTPRequestHandler, \
  SimpleHTTPRequestHandler

from .archive import Zip, Tar

BUFFER_SIZE_BYTES = 4 * 1024 * 1024  # 4MB
FORMAT_TO_ARCHIVE = {
  'zip': Zip,
  'tar': Tar,
}


class ListingsServer(DTProcess, ThreadingHTTPServer):

  def __init__(self, bind, data_dir):
    # get data directory
    os.chdir(data_dir)
    # ---
    DTProcess.__init__(self)
    ThreadingHTTPServer.__init__(self, bind, SimpleHTTPRequestHandler)
    # ---
    self.logger.info(f'Ready to accept requests on {bind[0]}:{bind[1]}.')

  def shutdown(self):
    ThreadingHTTPServer.shutdown(self)
    DTProcess.shutdown(self)



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
    self.logger.info(f'Ready to accept requests on {bind[0]}:{bind[1]}.')

  def shutdown(self):
    ThreadingHTTPServer.shutdown(self)
    DTProcess.shutdown(self)



class FilesAPIHTTPRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def set_headers(self, code, message, content_length, mime_type='text/plain', mime_enc=None):
        # open headers
        self.send_response(code, message)
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
        filepath_req, args_str = parts[0], parts[1]
        args = parse_args(args_str)
        # check arguments
        if 'format' in args and args['format'] not in FORMAT_TO_ARCHIVE:
            self.send_error(400, 'Bad Request', f'Format {args["format"]} not supported.')
        # get requested file from request object
        filepath = os.path.join(self.server.data_dir, filepath_req[1:])
        self.server.logger.debug(f'Requesting: GET:[{filepath_req}]')
        # check if the path exists
        if not os.path.exists(filepath):
            self.send_error(404, 'Not Found', f'Resource {filepath_req} not found.')
        # we can't deliver directories without an archive format
        if 'format' not in args and os.path.isdir(filepath):
            self.send_error(400, 'Bad Request', f'Path {filepath_req} is a directory. A format is required.')
        # deliver files on match
        if 'format' not in args and os.path.isfile(filepath):
            # figure out the MIME type/enc for the requested file
            mime_type, mime_enc = mimetypes.guess_type(filepath)
            # get file size
            content_length = os.path.getsize(filepath)
            # send headers
            self.set_headers(200, 'OK', content_length, mime_type, mime_enc)
            # send file
            with open(filepath, 'rb') as fin:
              transfer_bytes(fin, self.wfile)
            return
        # compress the resource
        archive = FORMAT_TO_ARCHIVE[args['format']]()
        archive.add(filepath, filepath_req)
        mime_type, mime_enc = archive.mime()
        # return archive
        self.set_headers(200, 'OK', archive.size(), mime_type, mime_enc)
        # send file
        transfer_bytes(archive.data(), self.wfile)

    def do_POST(self):
        # get requested file from request object
        file = self.path
        self.server.logger.debug(f'Requesting: POST:[{file}] w/ args {None}')
        self.set_headers()

    def do_HEAD(self):
        self.server.logger.debug(f'Requesting: HEAD')
        self.set_headers()

    def log_message(self, format, *args):
        return


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
