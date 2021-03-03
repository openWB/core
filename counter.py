"""Zähler-Logik
"""

import data


class counter():
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

    @property
    def evu_get_power_all(self):
        try:
            return self._data["evu"]["get"]["power_all"]
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in evu_get_power_all")
            return False

class counterModule():
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