import functools
import threading
import requests
from collections import defaultdict
from enum import Enum
from typing import Union
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from core._config import _const
from core._config._exception import HttpConfigException
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
             protocol=None) -> requests.models.Response:
        self.method = method or self._method
        self.domain = domain or self.domain
        self.path = path or self.path
        self.params = params or self.params
        self.data = data or self.data
        self.json = json or self.json
        self.headers = headers or self.headers
        self.protocol = protocol or self.protocol
        self.result = self.session.request(self.method, self._get_url(), params=self.params, data=self.data,
                                           json=self.json,
                                           headers=self.headers)
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
        return self._keys.copy()

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
