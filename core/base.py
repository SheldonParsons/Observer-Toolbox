from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Union, Any
from core.utils import Sender, IndexableDict, HiddenDefaultDict


class Parameter:

    def __getattr__(self, item):
        return None


class RunnerResultBase:
    pass


class Server(ABC):
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
    def run(self, *args, **kwargs) -> RunnerResultBase:
        pass


ServerType = TypeVar('ServerType', bound=Server)


class ServerStock(Generic[ServerType]):

    def __init__(self, stock: IndexableDict, args_mapping) -> None:
        self.current = 0
        self.stock = stock
        self.args_mapping = args_mapping

    def __iter__(self):
        return self

    def __next__(self) -> ServerType:
        try:
            server_class, server_parameter_class = self.stock.get_item(self.current)
            self.current += 1
            server_instance: Server = server_class()
            server_instance.parameter = server_parameter_class(**self.args_mapping)
            return server_instance
        except IndexError:
            raise StopIteration
