"""Ladepunkt-Logik
"""

import data


class chargepoint():
    """ geht alle Ladepunkte durch, prüft, ob geladen werden darf und ruft die Funktion des angesteckten Autos auf. 
    """

    data={}

    def __init__(self):
        pass

    def __is_cp_available(self):
        """ prüft, ob sich der LP in der vorgegebenen Zeit zurückgemeldet hat.
        """
        pass

    def __is_cp_locked(self):
        """prüft, ob der LP gesperrt ist
        """
        pass

    def get_state(self):
        """prüft alle Bedingungen und ruft die EV-Logik auf
        """
        try:
            if self.__is_cp_available()==True:
                if data["get"]["plug_state"]==True:
                    if self.__is_cp_locked()==True:
                        if data["get"]["autolock_active"]==False:
                            return True
        except:
            print("Some topics missing")
            return False
        return False


class cpTemplate():
    """ Vorlage für einen LP.
    """
    data={}
