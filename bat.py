"""Hausspeicher-Logik
"""

import data


class batModule():
    """
    """

    def __init__(self):
        self._data={}

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data