"""Ladepunkt-Logik
"""

import data

class allChargepoints():
    """
    """
    
    def __init__(self):
        self.data={}

class chargepoint():
    """ geht alle Ladepunkte durch, prüft, ob geladen werden darf und ruft die Funktion des angesteckten Autos auf. 
    """

    def __init__(self):
        self.data={}

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
                if self.data["get"]["plug_state"]==True:
                    if self.__is_cp_locked()==True:
                        if self.data["get"]["enabled"]==False:
                            return True
        except:
            print("dictionary key doens't exist")
            return False
        return False


class cpTemplate():
    """ Vorlage für einen LP.
    """
    
    def __init__(self):
        self.data={}
