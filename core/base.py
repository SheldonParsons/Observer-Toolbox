from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Union, List

from core.monitor import MonitorBase
from core.root import SourceType
from core.utils import Sender, IndexingDict, HiddenDefaultDict, HttpProtocolEnum

T = TypeVar("T", bound=object)


class Parameter:

    def __getattr__(self, item):
        return None


class RunnerResult:

    def __init__(self, source_object: Union['Server', 'Plugin'], data=None):
        self.source_type = getattr(source_object, 'source_type', None) or str(type(source_object))
        self.source_name = getattr(source_object, 'source_name', None) or source_object.__class__.__name__
        self.data = data

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data


class Data:

    def __init__(self, obj, data, method_name):
        self.result: RunnerResult = data
        self.obj = obj
        self.method_name = method_name


class Server(ABC, metaclass=MonitorBase):
    source_type = SourceType.SERVER
    source_name = None
    __restrict_init__ = True

    def __init__(self, domain=None, protocol=HttpProtocolEnum.HTTP):
        self.sender = Sender(domain, protocol)
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

    def reset_sender(self, domain=None, protocol=None):
        self.sender = Sender(domain=domain or self.sender.domain, protocol=protocol or self.sender.protocol)

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
    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        pass


ServerType = TypeVar('ServerType', bound=Server)


def get_monitor_class(_class=None) -> List:
    _class = _class or Server
    for key, value in _class.__dict__.items():
        if callable(value) and key != "__init__":
            yield key


class Plugin(ABC, metaclass=MonitorBase):
    source_type = SourceType.PLUGIN
    source_name = None
    plugin_allow_monitor_functions = ["run"]
    allow_monitor_functions = []

    @abstractmethod
    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        pass

    def get_notify(self, data: Data):
        pass


class ServerPlugin(Plugin):
    """
    监听服务类型的插件统一继承的父类
    """
    server_allow_monitor_functions = ["initialize", "run"]

    def run(self, *args, **kwargs) -> Union[RunnerResult, T]:
        raise NotImplementedError("插件子类必须实现 run 方法！")


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
