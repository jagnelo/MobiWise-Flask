KEY_SUCCESS = "success"
KEY_MESSAGE = "message"
KEY_ERROR = "error"
KEY_CONTENT = "content"


def success_response(msg: str = None, content: dict = None):
    r = {KEY_SUCCESS: True}
    if msg is not None:
        r[KEY_MESSAGE] = msg
    if content is not None:
        r[KEY_CONTENT] = content
    return r


def error_response(error: str = None, content: dict = None):
    r = {KEY_SUCCESS: False}
    if error is not None:
        r[KEY_ERROR] = error
    if content is not None:
        r[KEY_CONTENT] = content
    return r
