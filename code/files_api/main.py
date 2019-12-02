import os
import sys
import signal
import threading
from files_api import applogger, FilesAPI, ListingsServer
from dt_avahi_utils import enable_service, disable_service

LISTINGS_PORT = 8082
API_PORT = 8083
DEFAULT_DATA_DIR = '/data'
_is_shutdown = False


def main():
  data_dir = os.environ['DATA_DIR'] if 'DATA_DIR' in os.environ else DEFAULT_DATA_DIR
  wd = os.getcwd()

  # Start the server in a new thread
  applogger.info('Starting Listings server...')
  listings_httpd = ListingsServer(('', LISTINGS_PORT), data_dir)
  listings_daemon = threading.Thread(name='files_listings_server', target=listings_httpd.serve_forever)
  listings_daemon.setDaemon(True)
  enable_service('dt.files-listings')
  listings_daemon.start()
  os.chdir(wd)

  # Start the files API
  applogger.info('Starting API server...')
  files_api = FilesAPI(('', API_PORT), data_dir)
  api_daemon = threading.Thread(name='files_api_server', target=files_api.serve_forever)
  api_daemon.setDaemon(True)
  enable_service('dt.files-api')
  api_daemon.start()

  # define shutdown procedure
  def shutdown(*args):
    global _is_shutdown
    if _is_shutdown:
      return
    _is_shutdown = True
    applogger.info('Shutting down...')
    listings_httpd.shutdown()
    files_api.shutdown()
    # Block on the threads
    listings_daemon.join()
    disable_service('dt.files-listings')
    api_daemon.join()
    disable_service('dt.files-api')

  # wait for shutdown signal
  signal.signal(signal.SIGINT, shutdown)
  signal.pause()


if __name__ == '__main__':
  main()
