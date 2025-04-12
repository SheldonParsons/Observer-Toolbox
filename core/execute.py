from typing import Optional, Union, List

import servers
import inner_plugins
from core.generator import PluginPool, GlobalData
from core.deco import server_stock

__all__ = ["servers", "inner_plugins"]

from core.base import ServerStock, Server, SystemContext, SystemParameters
from core.utils import RunnerParameter
from core.generator import ServicePlugin


def _runner(args: Optional[Union[List[Union[str, int]]]], plugins: List[ServicePlugin]):
    args_mapping = RunnerParameter(args).get_args_mapping()
    system_parameters = SystemParameters(**args_mapping)
    GlobalData.system_parameters = system_parameters
    with SystemContext(system_parameters.clean_temp_files):
        stock = ServerStock[Server](server_stock, args_mapping)
        list(PluginPool.register(plugin) for plugin in plugins or [])
        list(server.run() for server in stock)
        list(plugin.run() for plugin in PluginPool.get_plugins())
