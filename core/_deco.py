import functools
from core.utils import IndexableDict

server_stock = IndexableDict()


class ServerRunner:
    def __init__(self, parameter=None):
        self.parameter = parameter

    def __call__(self, cls):
        global server_stock
        server_stock[cls] = self.parameter

        @functools.wraps(cls)
        def wrapper(*args, **kwargs):
            return cls(*args, **kwargs)

        return wrapper