import mimetypes
from dt_class_utils import DTProcess
from http.server import BaseHTTPRequestHandler, HTTPServer



class FilesAPI(DTProcess):

  def __init__(self, data_dir, port):
    DTProcess.__init__(self)
    # get data directory
    self.data_dir = data_dir
    # get list of excluded files
    self.exclude_paths = map(
      lambda s: s.strip(),
      (os.environ['EXCLUDE_PATHS'] if 'EXCLUDE_PATHS' in os.environ else "").split(',')
    )
    # http server
    self.httpd = FilesAPIHTTPServer(port)


  def serve_forever(self):
    while not self.is_shutdown:
      try:
        self.httpd.handle_request()
      except:
        pass



class FilesAPIHTTPServer(HTTPServer):

    def __init__(self, server_address):
        HTTPServer.__init__(self, server_address, FilesAPIHTTPRequestHandler)



class FilesAPIHTTPRequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self, mime_type, mime_enc):
        # open headers
        self.send_response(200)

        self.send_header('Content-type', mime_type)
        self.send_header('Content-Encoding', mime_enc)


        # support CORS
        if 'Origin' in self.headers:
            self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])
        # close headers
        self.end_headers()

    def do_GET(self):
        file = self.path
        print('Requesting: [{}]'.format(file))
        # TODO: get file from request object
        mime_type, mime_enc = mimetypes.guess_type(file)
        self._set_headers()


        # code_loader_status = self.server.code_loader.get_status()
        # if not INCLUDE_OUTPUT:
        #     for lvl in code_loader_status['progress']:
        #         code_loader_status['progress'][lvl]['output'] = None
        # res = json.dumps(code_loader_status, indent=4, sort_keys=True).encode()


        self.wfile.write('Got: '+file)

    def do_HEAD(self):
        self._set_headers()

    def log_message(self, format, *args):
        return
