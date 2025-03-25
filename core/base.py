from abc import ABC, abstractmethod

from core.utils import Sender


class Parameter:
    pass


class Server(ABC):

    def __init__(self, domain=None, protocol=None):
        self.domain = domain
        self.sender = Sender(self.domain, protocol)

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
    def run(self, *args, **kwargs) -> None:
        pass


from typing import TypeVar, Generic, List

ServerType = TypeVar('ServerType')


class ServerStock(Generic[ServerType]):

    def __init__(self, stock: List[ServerType]) -> None:
        self.current = 0
        self.stock = stock

    def __iter__(self):
        return self

    def __next__(self) -> ServerType:
        try:
            res = self.stock[self.current]
            self.current += 1
            return res
        except IndexError:
            raise StopIteration
