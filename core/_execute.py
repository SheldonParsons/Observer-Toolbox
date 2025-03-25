from typing import Optional, Union, List

import servers
from core._deco import server_stock

__all__ = ["servers"]

from core.base import ServerStock, Server, Parameter
from core.utils import RunnerParameter


def _runner(args: Optional[Union[List[Union[str, int]]]]):
    args_mapping = RunnerParameter(args).args_mapping
    stock = ServerStock[Server](server_stock)
    for server in stock:
        parameter:Parameter = server.parameter(**args_mapping)
        res, result_dict = server(parameter).run()
        print(result_dict)

