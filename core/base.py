import os
import shutil
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Union, List

from core._config import _const
from core._config._exception import TempFileTypeException, FileControlException, FileException
from core.monitor import MonitorBase
from core.root import SourceType, get_base_dir
from core.utils import Sender, IndexingDict, HiddenDefaultDict, HttpProtocolEnum, singleton

T = TypeVar("T", bound=object)


class Parameter:

    def __getattr__(self, item):
        return None


class EmptyParameter(Parameter):

    def __init__(self, *args, **kwargs):
        pass


@singleton
class SystemParameters(Parameter):

    def __init__(
            self,
            clean_temp_files: str = '2',
            kdocs_files_path: Union[str, List] = None,
            close_inner_all: str = '2',
            report_type: str = None,
            reviewer: str = None,
            env: List = None,
            test_type: str = None,
            real_result: str = None,
            project_risk: str = None,
            font_name: str = None,
            test_result_text: str = None,
            sender: str = None,
            out_put_dir: str = None,
            *args,
            **kwargs
    ):
        def parse_bool_param(param, default=False) -> bool:
            try:
                if isinstance(param, bool):
                    return param
                return str(param).strip() == '1'
            except (TypeError, ValueError, AttributeError):
                return default

        # 参数处理解耦
        self.clean_temp_files = parse_bool_param(clean_temp_files, default=True)
        self.close_inner_all = parse_bool_param(close_inner_all, default=False)
        self.kdocs_files_path = kdocs_files_path
        self.report_type = report_type
        self.test_result_text = test_result_text
        self.test_type = test_type
        self.real_result = real_result
        self.project_risk = project_risk
        self.font_name = font_name
        self.reviewer = reviewer
        self.sender = sender
        self.out_put_dir = out_put_dir
        self.env = env
        self.strict_mode: bool = False


class RunnerResult:
    __slots__ = ('source_type', 'source_name', '_data', '_initialized')

    def __init__(self, source_object: Union['Server', 'Plugin'], data=None):
        super().__setattr__('_initialized', False)
        self.source_type = getattr(source_object, 'source_type', None) or str(type(source_object))
        self.source_name = getattr(source_object, 'source_name', None) or source_object.__class__.__name__
        self._data = data
        super().__setattr__('_initialized', True)

    def get_data(self):
        return self._data

    def __setattr__(self, name, value):
        if getattr(self, '_initialized', False):
            raise AttributeError(
                f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        if hasattr(self, name):
            raise AttributeError(
                f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")
        else:
            raise AttributeError(
                f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")

    def __setitem__(self, key, value):
        raise TypeError(
            f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")

    def __delitem__(self, key):
        raise TypeError(
            f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")


class Data:
    __slots__ = ('result', 'obj', 'method_name', '_initialized')

    def __init__(self, obj, data, method_name):
        super().__setattr__('_initialized', False)
        self.result: RunnerResult = data
        self.obj = obj
        self.method_name = method_name
        super().__setattr__('_initialized', True)

    def __setattr__(self, name, value):
        if getattr(self, '_initialized', False):
            raise AttributeError(
                f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        if hasattr(self, name):
            raise AttributeError(
                f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")
        else:
            raise AttributeError(
                f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")

    def __setitem__(self, key, value):
        raise TypeError(
            f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")

    def __delitem__(self, key):
        raise TypeError(
            f"{self.__class__.__name__} 属性不可变，请勿修改广播对象的值，该操作有可能会影响后续的监听服务。")


class Server(ABC, metaclass=MonitorBase):
    source_type = SourceType.SERVER
    source_name = None
    __restrict_init__ = True

    def __init__(self, domain=None, protocol=HttpProtocolEnum.HTTP):
        self.sender = Sender(domain, protocol)
        self.parameter: Union[Parameter, dict] = HiddenDefaultDict(None)

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

    @classmethod
    @abstractmethod
    def ping(cls) -> bool:
        """测试服务，请使用最小信息验证服务是否正常"""
        pass

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
        pass


class ServerStock(Generic[ServerType]):

    def __init__(self, stock: IndexingDict, args_mapping, include_inner_servers: bool = True) -> None:
        self.current = 0
        if include_inner_servers:
            import servers
            self.stock = stock.sort(getattr(servers, '__all__', stock))
        else:
            self.stock = stock
        self.args_mapping = args_mapping

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.stock)

    def __next__(self) -> Union[ServerType, str]:
        try:
            server_class, server_parameter_class = self.stock.get_item(self.current)
            self.current += 1
            parameter = server_parameter_class(**self.args_mapping)
            server_instance = server_class()
            server_instance.parameter = parameter
            server_instance.initialize()
            return server_instance
        except IndexError:
            raise StopIteration


class SystemContext:

    def __init__(self, clean_temp_files_on_end: bool = True) -> None:
        self.path = get_base_dir()
        self.clean_temp_files_on_end = clean_temp_files_on_end

    def _safe_clear_directory(self):
        try:
            if not os.path.exists(self.path):
                os.makedirs(self.path, exist_ok=True)
            if not os.path.isdir(self.path):
                raise TempFileTypeException(_const.EXCEPTION.TEMP_FILE_NOT_FOUND_Exception % (str(self.path),))

            for entry in os.listdir(self.path):
                path = os.path.join(self.path, entry)
                try:
                    if os.path.isfile(path) or os.path.islink(path):
                        os.unlink(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                except Exception as e:
                    raise FileControlException(_const.EXCEPTION.TEMP_File_Control_Exception % (path, str(e),))

        except Exception as e:
            raise FileException(_const.EXCEPTION.Contxt_Exception % (str(e),))

    def __enter__(self):
        self._safe_clear_directory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.clean_temp_files_on_end:
            self._safe_clear_directory()
