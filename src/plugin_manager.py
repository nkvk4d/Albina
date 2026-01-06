from abc import ABC, abstractmethod
from enum import Enum, EnumDict


class AlbinaEvent(EnumDict):
    COMMAND: str


class AlbinaManager:
    def __init__(self):
        pass

class AlbinaUI(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def change_color(self, color):
        pass

    @abstractmethod
    def print(self, text):
        pass

class AlbinaCommand(ABC):
    @abstractmethod
    def __call__(self, args):
        pass

class AlbinaListener(ABC):
    @abstractmethod
    def __call__(self) -> AlbinaEvent:
        pass
