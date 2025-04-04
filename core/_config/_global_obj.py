import functools
import threading


def singleton(cls):
    instances = {}
    lock = threading.Lock()

    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class _PluginPool:

    def __init__(self):
        self.plugins = []

    def register(self, plugin):
        print(f"plugin-plugin:{plugin}")
        self.plugins.append(plugin)

    def get_plugins(self):
        return self.plugins


def _get_plugin_pool() -> _PluginPool:
    return _PluginPool()


PluginPool = _get_plugin_pool()
