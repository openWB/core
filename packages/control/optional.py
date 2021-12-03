"""Optionale Module
"""

from math import ceil  # Aufrunden

from helpermodules.log import MainLogger


class Optional:
    def __init__(self):
        try:
            self.data = {"et": {"get": {}}}
        except Exception:
            MainLogger().exception("Fehler im Optional-Modul")

    def et_price_lower_than_limit(self):
        """ prüft, ob der aktuelle Strompreis unter der festgelegten Preisgrenze liegt.

        Return
        ------
        True: Preis liegt darunter
        False: Preis liegt darüber
        """
        try:
            if self.data["et"]["get"]["price"] <= self.data["et"]["config"][
                    "max_price"]:
                return True
            else:
                return False
        except Exception:
            self.et_get_prices()
            MainLogger().exception("Fehler im Optional-Modul")
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
            price_list = self.data["et"]["get"]["price_list"]
            return [
                i[0] for i in sorted(price_list, key=lambda x: x[1])
                [:ceil(duration)]
            ]
        except Exception:
            self.et_get_prices()
            MainLogger().exception("Fehler im Optional-Modul")
            return []

    def et_get_prices(self):
        try:
            if self.data["et"]["active"]:
                # if self.data["et"]["config"]["provider"]["provider"] == "awattar":
                #     awattargetprices.update_pricedata(
                #         self.data["et"]["config"]["provider"]["country"], 0)
                # elif self.data["et"]["config"]["provider"]["provider"] == "tibber":
                #     tibbergetprices.update_pricedata(
                #         self.data["et"]["config"]["provider"]["token"], self.data["et"]["config"]["provider"]["id"])
                # else:
                MainLogger().error("Unbekannter Et-Provider.")
        except Exception:
            MainLogger().exception("Fehler im Optional-Modul")
