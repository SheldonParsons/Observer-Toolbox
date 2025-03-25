import functools

server_stock = []


def ServerRunner(parameter=None):
    def _warpper(cls):
        global server_stock
        setattr(cls, "parameter", parameter)
        server_stock.append(cls)

        @functools.wraps(cls)
        def _inner(*args, **kwargs):
            return cls(*args, **kwargs)

        return _inner

    return _warpper
