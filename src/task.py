import os
from enum import Enum

from spopen import SPopen


class RunMode(Enum):
    Sequential = 0
    Parallel = 1
    IsolatedParallel = 2


class Task:
    def __init__(self):
        self.cwd = os.getcwd()
        self.env = os.environ.copy()

    def get_run_mode(self) -> RunMode:
        raise NotImplementedError

    def run(self, process: SPopen):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError
