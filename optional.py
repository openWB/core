"""Optionale Module
"""

from heapq import nsmallest 
from math import ceil #Aufrunden

import data


class optional():
    """
    """

    data={}

    def __init__(self):
        pass

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
            pricedict = self.data["et"]["get"]["pricedict"]
            return nsmallest(ceil(duration), pricedict, key = pricedict.get)
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in get_loading_hours")
            return ()