import os
import mimetypes
from dt_class_utils import DTProcess
from http.server import \
  ThreadingHTTPServer, \
  BaseHTTPRequestHandler, \
  SimpleHTTPRequestHandler

BUFFER_SIZE_BYTES = 4 * 1024 * 1024  # 4MB


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

    def _set_headers(self, code, content_length, mime_type='text/plain', mime_enc=None):
        # open headers
        self.send_response(code)
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
        # get requested file from request object
        filepath = os.path.join(self.server.data_dir, self.path)
        self.server.logger.debug(f'Requesting: GET:[{filepath}]')
        # deliver files on match
        if os.path.exists(filepath) and os.path.isfile(filepath):
            # figure out the MIME type/enc for the requested file
            mime_type, mime_enc = mimetypes.guess_type(filepath)
            # get file size
            content_length = os.path.getsize(filepath)
            # send headers
            self._set_headers(200, content_length, mime_type, mime_enc)
            # send file
            with open(filepath, 'rb') as fin:
              self.wfile.write(fin.read(BUFFER_SIZE_BYTES))
            return
        # the filepath is not an existing file
        # if os.path.exists(filepath) and os.path.isdir(filepath):
        #







        # code_loader_status = self.server.code_loader.get_status()
        # if not INCLUDE_OUTPUT:
        #     for lvl in code_loader_status['progress']:
        #         code_loader_status['progress'][lvl]['output'] = None
        # res = json.dumps(code_loader_status, indent=4, sort_keys=True).encode()


        # self.wfile.write('Got: '+file)

    def do_POST(self):
        # get requested file from request object
        file = self.path
        self.server.logger.debug(f'Requesting: POST:[{file}] w/ args {None}')
        self._set_headers()

    def do_HEAD(self):
        self.server.logger.debug(f'Requesting: HEAD')
        self._set_headers()

    def log_message(self, format, *args):
        return
