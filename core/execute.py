from typing import Optional, Union, List

from core.generator import PluginPool, GlobalData
from core.deco import server_stock
import servers, inner_plugins
from core.base import ServerStock, Server, SystemContext, SystemParameters
from core.utils import RunnerParameter
from core.generator import ServicePlugin


def _runner(args: Optional[Union[List[Union[str, int]]]], plugins: List[ServicePlugin]):
    args_mapping = RunnerParameter(args).get_args_mapping()
    system_parameters = SystemParameters(**args_mapping)
    if system_parameters.close_inner_all is True:
        clean_inner_observers()
    GlobalData.system_parameters = system_parameters
    with SystemContext(system_parameters.clean_temp_files):
        stock = ServerStock[Server](server_stock, args_mapping)
        list(PluginPool.register(plugin) for plugin in plugins or [])
        list(server.run() for server in stock)
        list(plugin.run() for plugin in PluginPool.get_plugins())


def clean_inner_observers():
    for key in server_stock.keys():
        if key.__name__ in getattr(servers, '__all__', None) or []:
            del server_stock[key]
    PluginPool.set_plugins(
        [plugin for plugin in PluginPool.get_plugins() if
         type(plugin).__name__ not in getattr(inner_plugins, '__all__', [])])
