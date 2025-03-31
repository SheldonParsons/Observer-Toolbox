from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Union, List

from core.monitor import MonitorBase
from core.utils import Sender, IndexingDict, HiddenDefaultDict


def get_monitor_class(_class) -> List:
    for key, value in _class.__dict__.items():
        if callable(value) and key != "__init__":
            yield key


class Data:

    def __init__(self, obj, data, method_name):
        self.data = data
        self.obj = obj
        self.method_name = method_name


class Parameter:

    def __getattr__(self, item):
        return None


class BaseRunnerResult:
    pass


class Server(ABC, metaclass=MonitorBase):

    def __init__(self, **kwargs):
        self.sender = Sender(**kwargs)
        self.parameter: Union[Parameter, dict] = HiddenDefaultDict(None)
        self.initialize()

    def initialize(self):
        """
        如果逻辑不符请进行重写，该方法为默认初始化
        :return:
        """
        self.set_base_headers()
        self.tokenization()
        self.set_tokenization_headers()

    @abstractmethod
    def set_base_headers(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def tokenization(self) -> bool:
        pass

    @abstractmethod
    def set_tokenization_headers(self):
        pass

    @abstractmethod
    def run(self, *args, **kwargs) -> BaseRunnerResult:
        pass


ServerType = TypeVar('ServerType', bound=Server)


class ServerStock(Generic[ServerType]):

    def __init__(self, stock: IndexingDict, args_mapping) -> None:
        self.current = 0
        self.stock = stock
        self.args_mapping = args_mapping

    def __iter__(self):
        return self

    def __next__(self) -> Union[ServerType, str]:
        try:
            server_class, server_parameter_class = self.stock.get_item(self.current)
            self.current += 1
            server_instance: Server = server_class()
            server_instance.parameter = server_parameter_class(**self.args_mapping)
            return server_instance
        except IndexError:
            raise StopIteration
