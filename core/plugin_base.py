from abc import ABC, abstractmethod

from core.base import BaseRunnerResult, get_monitor_class, Server, Data
from core.monitor import MonitorBase


class Plugin(ABC, metaclass=MonitorBase):
    plugin_monitor_functions = ["run"]

    @abstractmethod
    def run(self, *args, **kwargs) -> BaseRunnerResult:
        pass

    @abstractmethod
    def get_data(self, data: Data):
        pass


class ServerPlugin(Plugin):
    server_monitor_functions = list(get_monitor_class(Server))

    def run(self, *args, **kwargs) -> BaseRunnerResult:
        raise NotImplementedError("not implemented")

    def get_data(self, data: Data):
        raise NotImplementedError("not implemented")
