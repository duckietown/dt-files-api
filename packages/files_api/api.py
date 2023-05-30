from flask import Flask
from flask_cors import CORS

from .actions import data
# from .actions import backup
from .actions import calibration


class FilesAPI(Flask):

    def __init__(self):
        super(FilesAPI, self).__init__(__name__)
        self.url_map.strict_slashes = False
        # register blueprints
        self.register_blueprint(data)
        # self.register_blueprint(backup)
        self.register_blueprint(calibration)
        # apply CORS settings
        CORS(self)


__all__ = [
    'FilesAPI'
]
