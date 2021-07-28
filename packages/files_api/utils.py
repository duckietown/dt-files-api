from flask import jsonify


def _custom_response(status_code, message):
    response = jsonify({'message': message})
    response.status_code = status_code
    return response


def bad_request(message):
    return _custom_response(400, message)


def not_found(message):
    return _custom_response(404, message)


def ok():
    return _custom_response(200, "OK")


def transfer_bytes(bytes_in, socket_out):
    while True:
        chunk = bytes_in.read(4096)
        if not chunk:
            break
        socket_out.write(chunk)


class AppException(BaseException):

    def __init__(self, message: str):
        super(AppException, self).__init__(message)
        self._message = message

    @property
    def message(self):
        return self._message


__all__ = [
    "bad_request",
    "not_found",
    "ok",
    "transfer_bytes",
    "AppException"
]
