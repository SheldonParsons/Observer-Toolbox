from typing import Optional, Union, List

import servers
import inner_plugins
from core._config import PluginPool
from core.deco import server_stock

__all__ = ["servers", "inner_plugins"]

from core.base import ServerStock, Server
from core.utils import RunnerParameter


def _runner(args: Optional[Union[List[Union[str, int]]]]):
    args_mapping = RunnerParameter(args).get_args_mapping()
    stock = ServerStock[Server](server_stock, args_mapping)
    list(server.run() for server in stock)
    list(plugin.run() for plugin in PluginPool.get_plugins())
