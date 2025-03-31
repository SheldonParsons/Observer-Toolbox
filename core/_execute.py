from typing import Optional, Union, List

import servers
from core._config import PluginPool
from core._deco import server_stock

__all__ = ["servers"]

from core.base import ServerStock, Server
from core.utils import RunnerParameter


def _runner(args: Optional[Union[List[Union[str, int]]]]):
    args_mapping = RunnerParameter(args).get_args_mapping()
    stock = ServerStock[Server](server_stock, args_mapping)
    for server in stock:
        result = server.run()
        print(result)

    for plugin in PluginPool.get_plugins():
        plugin.run()
