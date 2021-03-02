"""Allgemeine Einstellungen
"""

import data


class general():
    """
    """

    def __init__(self):
        self.data={}

    def get_phases_chargemode(self, chargemode):
        """ gibt die Anazhl Phasen zurück, mit denen im jeweiligen Lademodus geladen wird

        Parameter
        ---------
        chargemode: str
            Lademodus
        
        Return
        ------
        int: Anzahl Phasen
        """
        try:
            return self.data["chargemode_config"][chargemode]["phases_to_use"]
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in get_phases_chargemode")
            return 1