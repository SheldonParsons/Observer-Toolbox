import functools
import threading

import requests
from collections import defaultdict
from collections.abc import Mapping
from enum import Enum
from typing import Union, List, Callable
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from core._config import _const
from core._config._exception import HttpConfigException, ModuleNotFoundException
from urllib.parse import urljoin


class HttpMethodEnum(str, Enum):
    GET = 'get'
    POST = 'post'
    PATCH = 'patch'
    DELETE = 'delete'
    HEAD = 'head'


class HttpProtocolEnum(str, Enum):
    HTTP = "http://"
    HTTPS = "https://"


retries = Retry(
    total=3,
    backoff_factor=1,
)


class Sender:

    def __init__(self, domain=None, protocol=HttpProtocolEnum.HTTP):
        adapter = HTTPAdapter(max_retries=retries)
        self.session = requests.Session()
        [self.session.mount(proxy, adapter) for proxy in _const.HTTP_CONFIG.adapters]
        self._method = HttpMethodEnum.GET
        self._domain = domain
        self._path = None
        self._data = None
        self._json = None
        self._params = {}
        self._headers = {}
        self._protocol = protocol or HttpProtocolEnum.HTTP
        self._result = None
        self._stream = False

    @property
    def stream(self):
        return self._stream

    @stream.setter
    def stream(self, value):
        self._stream = value

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        self._result = value

    @property
    def method(self) -> str:
        return self._method.value

    @method.setter
    def method(self, value: HttpMethodEnum) -> None:
        self._method = value

    @property
    def domain(self) -> str:
        return self._domain

    @domain.setter
    def domain(self, value: str) -> None:
        self._domain = value

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, value: str) -> None:
        self._path = value

    @property
    def data(self) -> Union[dict, str]:
        return self._data

    @data.setter
    def data(self, value: Union[dict, str]) -> None:
        self._data = value

    @property
    def json(self) -> str:
        return self._json

    @json.setter
    def json(self, value: dict):
        if isinstance(value, dict) is False:
            raise HttpConfigException(_const.EXCEPTION.HTTP_JSON_DATA_NOT_SUPPORTED % (str(type(value)), str(value)))
        self._json = value

    @property
    def params(self) -> dict:
        return self._params

    @params.setter
    def params(self, value: dict) -> None:
        if isinstance(value, dict) is False:
            raise HttpConfigException(_const.EXCEPTION.HTTP_PARAMS_NOT_SUPPORTED % (str(type(value)), str(value)))
        self._params = value

    @property
    def headers(self) -> dict:
        return self._headers

    @headers.setter
    def headers(self, value: dict):
        if isinstance(value, dict) is False:
            raise HttpConfigException(_const.EXCEPTION.HTTP_HEADERS_NOT_SUPPORTED % (str(type(value)), str(value)))
        self._headers = value

    @property
    def protocol(self) -> HttpProtocolEnum:
        return self._protocol

    @protocol.setter
    def protocol(self, value: HttpProtocolEnum) -> None:
        self._protocol = value

    def clean_params(self) -> None:
        self.params = {}

    def patch_headers(self, patch_mapping: dict):
        for key, value in patch_mapping.items():
            self._headers[key] = value

    def _get_url(self) -> str:
        if isinstance(self._protocol, HttpProtocolEnum) is False:
            raise HttpConfigException(_const.EXCEPTION.HTTP_PROTOCOL_NOT_SUPPORTED)
        if isinstance(self._domain, str) is False:
            raise HttpConfigException(_const.EXCEPTION.HTTP_DOMAIN_NOT_SUPPORTED % (str(self._domain, )))
        if isinstance(self._path, str) is False:
            raise HttpConfigException(_const.EXCEPTION.HTTP_PATH_NOT_SUPPORTED % (str(self._path, )))
        return urljoin(self._protocol.value + self._domain, self._path)

    def send(self, method=None, domain=None, path=None, params=None, data=None, json=None, headers=None,
             protocol=None, stream=False, filter_callback: Union[Callable[[dict], List]] = None,
             target: str = None) -> Union[requests.models.Response, List]:
        self.method = method or self._method
        self.domain = domain or self.domain
        self.path = path or self.path
        self.params = params or self.params
        self.data = data or self.data
        self.json = json or self.json
        self.headers = headers or self.headers
        self.protocol = protocol or self.protocol
        self.stream = stream
        self.result = self.session.request(self.method, self._get_url(), params=self.params, data=self.data,
                                           json=self.json,
                                           headers=self.headers, stream=stream)
        if self.stream and filter_callback is not None and target is not None:
            self.result.raw.decode_content = True
            try:
                import ijson
            except ModuleNotFoundError as e:
                raise ModuleNotFoundException(
                    _const.EXCEPTION.Module_Not_Found_Exception % ('ijson', 'pip install ijson==3.3.0', str(e),))
            bugs_generator = ijson.items(self.result.raw, target)
            return [bug for bug in bugs_generator if filter_callback(bug)]
        return self.result


class HiddenDefaultDict(defaultdict):
    def __init__(self, default_factory=None, callback=None):
        super().__init__(default_factory)
        self.callback = callback

    def __setitem__(self, key, value):
        old_value = self.get(key, self.default_factory())
        super().__setitem__(key, value)
        if self.callback:
            self.callback(key, old_value, value)

    def __getattr__(self, item):
        if self.default_factory is None:
            return self.default_factory
        return super().__getattribute__(item)

    def __repr__(self):
        return dict.__repr__(self)


class RunnerParameter:

    def __init__(self, args: list):
        self.args_mapping = {}
        i = 0
        while i < len(args):
            if args[i].startswith(_const.SYMBOL.ParamsStartWithSymbol * 2):
                key = args[i].lstrip(_const.SYMBOL.ParamsStartWithSymbol)
                if i + 1 < len(args):
                    value = args[i + 1]
                    self.args_mapping[key] = value
                    i += 2
                    continue
            i += 1

    def get_args_mapping(self):
        return self.args_mapping


class DynamicFreezeObject(Mapping):
    def __getitem__(self, key):
        str_key = str(key)
        if str_key in self.__dict__:
            return self.__dict__[str_key]
        else:
            raise KeyError(f"Key '{key}' not found")

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        for key, value in self.__dict__.items():
            if isinstance(value, DynamicFreezeObject):
                yield key, dict(value)
            else:
                yield key, value

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            str_key = str(key) if not isinstance(key, str) else key
            if isinstance(value, dict):
                sanitized_dict = {str(k): v for k, v in value.items()}
                self.__dict__[str_key] = DynamicFreezeObject(**sanitized_dict)
            elif isinstance(value, list):
                self.__dict__[str_key] = tuple(value)
            else:
                self.__dict__[str_key] = value

    __annotations__ = {}

    def __getattr__(self, name: str):
        raise AttributeError(f"{self.__class__.__name__} 没有属性 '{name}'")

    def __repr__(self):
        return str(self.__dict__)

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

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return [(_ := lambda value: dict(value) if isinstance(value, DynamicFreezeObject) else value)(value) for value
                in
                self.__dict__.values()]

    def items(self):
        """ 返回键值对视图（可选） """
        return self.__dict__.items()


class IndexingDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._keys = list(super().keys())

    def __setitem__(self, key, value):
        if key not in self:
            self._keys.append(key)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        super().__delitem__(key)
        self._keys.remove(key)

    def __len__(self):
        return len(self._keys)

    def sort(self, sort_list: List[str]):
        """
        重排序
        :param sort_list:
        :return:
        """
        order_index = {name: i for i, name in enumerate(sort_list)}
        self._keys = sorted(self._keys, key=lambda x: order_index.get(x.__name__, float('inf')))
        return self

    def get_key(self, index):
        return self._keys[index]

    def get_value(self, index):
        return self[self._keys[index]]

    def get_item(self, index):
        key = self._keys[index]
        return (key, self[key])

    def update(self, other=(), **kwargs):
        for k, v in dict(other).items():
            self.__setitem__(k, v)
        for k, v in kwargs.items():
            self.__setitem__(k, v)

    def keys(self):
        return self._keys

    def values(self):
        return [self[key] for key in self._keys]

    def items(self):
        return [(key, self[key]) for key in self._keys]


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
