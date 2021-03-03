"""Optionale Module
"""

from heapq import nsmallest 
from math import ceil #Aufrunden

import data


class optional():
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
    def et_active(self):
        try:
            return self._data["et"]["active"]
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in get_et_active")
            return False
    
    def et_price_lower_than_limit(self):
        """ prüft, ob der aktuelle Strompreis unter der festgelegten Preisgrenze liegt.

        Return
        ------
        True: Preis liegt darunter
        False: Preis liegt darüber
        """
        try:
            if self._data["et"]["get"]["price"] < self._data["et"]["config"]["max_price"]:
                return True
            else:
                return False
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in et_price_lower_than_limit")
            return False

    def get_loading_hours(self, duration):
        """ geht die Preise der nächsten 24h durch und liefert eine Liste der Uhrzeiten, zu denen geladen werden soll

        Parameter
        ---------
        duration: float 
            benötigte Ladezeit
        
        Return
        ------
        list: Key des Dictionarys (Unix-Sekunden der günstigen Stunden)
        """
        try:
            pricedict = self._data["et"]["get"]["pricedict"]
            return nsmallest(ceil(duration), pricedict, key = pricedict.get)
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in get_loading_hours")
            return ()