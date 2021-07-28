from dt_class_utils import DTProcess, AppStatus

from files_api.api import FilesAPI
from files_api.constants import FILES_API_PORT


class FilesAPIApp(DTProcess):
    
    def __init__(self):
        super(FilesAPIApp, self).__init__('FilesAPI')
        self.status = AppStatus.RUNNING
        # serve HTTP requests over the REST API
        self._api = FilesAPI()
        self._api.run(host='0.0.0.0', port=FILES_API_PORT)


if __name__ == '__main__':
    app = FilesAPIApp()
