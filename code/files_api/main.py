import os
import threading
from files_api import FilesAPI
from dt_avahi_utils import enable_service, disable_service
from http.server import HTTPServer, CGIHTTPRequestHandler

LISTINGS_PORT = 8082
API_PORT = 8083
DEFAULT_DATA_DIR = '/data'

def main():
  data_dir = os.environ['DATA_DIR'] if 'DATA_DIR' in os.environ else DEFAULT_DATA_DIR
  wd = os.getcwd()

  # Start the server in a new thread
  os.chdir(data_dir)
  listings_httpd = HTTPServer(('', LISTINGS_PORT), CGIHTTPRequestHandler)
  listings_daemon = threading.Thread(name='files_listings_server', target=listings_httpd.serve_forever)
  listings_daemon.setDaemon(True)
  print('Starting Listings server...')
  enable_service('dt.files-listings')
  listings_daemon.start()
  os.chdir(wd)

  # Start the files API
  files_api = FilesAPI(data_dir, ('', API_PORT))
  api_daemon = threading.Thread(name='files_api_server', target=files_api.serve_forever)
  api_daemon.setDaemon(True)
  print('Starting API server...')
  enable_service('dt.files-api')
  api_daemon.start()

  # Block on the threads
  listings_daemon.join()
  disable_service('dt.files-listings')
  api_daemon.join()
  disable_service('dt.files-api')


if __name__ == '__main__':
  main()
