from flask import Flask
from flask_cors import CORS

from .actions import data
from .actions import backup


class FilesAPI(Flask):

    def __init__(self):
        super(FilesAPI, self).__init__(__name__)
        # register blueprints
        self.register_blueprint(data)
        self.register_blueprint(backup)
        # apply CORS settings
        CORS(self)


__all__ = [
    'FilesAPI'
]
