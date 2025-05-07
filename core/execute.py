from typing import Optional, Union, List

from core.generator import PluginPool, GlobalData
from core.deco import server_stock
from core.base import ServerStock, Server, SystemContext, SystemParameters
from core.utils import RunnerParameter
from core.generator import ServicePlugin
from servers.zendao_server import HelpAction


def _runner(args: Optional[Union[List[Union[str, int]]]], plugins: List[ServicePlugin]):
    args_mapping = RunnerParameter(args).get_args_mapping()
    help_action = HelpAction(**args_mapping)
    if help_action.get_info() is True:
        return
    system_parameters = SystemParameters(**args_mapping)
    if system_parameters.close_inner_all is False:
        import importlib
        importlib.import_module("servers")
        importlib.import_module("inner_plugins")
    else:
        PluginPool.set_include_inner_plugin(False)
    GlobalData.system_parameters = system_parameters
    with SystemContext(system_parameters.clean_temp_files):
        stock = ServerStock[Server](server_stock, args_mapping,
                                    include_inner_servers=system_parameters.close_inner_all is False)
        list(PluginPool.register(plugin) for plugin in plugins or [])
        list(server.run() for server in stock)
        if system_parameters.strict_mode is False and len(stock) > 0:
            list(plugin.run() for plugin in PluginPool.get_plugins())
