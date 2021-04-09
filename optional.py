"""Optionale Module
"""

from heapq import nsmallest 
from math import ceil #Aufrunden

import modules.et_awattar.awattargetprices as awattargetprices
import data
import log
import pub
import timecheck

class optional():
    """
    """

    def __init__(self):
        self.data={}
    
    def et_price_lower_than_limit(self):
        """ prüft, ob der aktuelle Strompreis unter der festgelegten Preisgrenze liegt.

        Return
        ------
        True: Preis liegt darunter
        False: Preis liegt darüber
        """
        try:
            self.et_get_prices()
            if self.data["et"]["get"]["price"] < self.data["et"]["config"]["max_price"]:
                return True
            else:
                return False
        except Exception as e:
            log.exception_logging(e)
            return False

    def et_get_loading_hours(self, duration):
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
            self.et_get_prices()
            pricedict = self.data["et"]["get"]["pricedict"]
            return nsmallest(ceil(duration), pricedict, key = pricedict.get)
        except Exception as e:
            log.exception_logging(e)
            return ()

    def et_get_prices(self):
        """
        """
        try:
            if timecheck.check_timestamp(self.data["et"]["set"]["timestamp_updated_prices"], 58*60) == False:
                if self.data["et"]["provider"] == "awattar":
                    awattargetprices.awattar_get_prices()
                    pub.pub_dict("etprovidergraphlist", "openWB/optional/et/get/pricedict")
                    pub.pub_float("etproviderprice", "openWB/optional/et/get/price")
                else:
                    log.message_debug_log("error", "Unbekannter Et-Provider.")
                self.data["et"]["set"]["timestamp_updated_prices"] = timecheck.create_timestamp()
                pub.pub("openWB/set/optional/et/set/timestamp_updated_prices", self.data["et"]["set"]["timestamp_updated_prices"])
        except Exception as e:
            log.exception_logging(e)