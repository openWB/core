"""Ladepunkt-Logik
"""

import data


class chargepoint(self):
    """ geht alle Ladepunkte durch, prüft, ob geladen werden darf und ruft die Funktion des angesteckten Autos auf. 
    """

    def __init__(self):
        self.ev=0
        self.template=0

    def __is_cp_configured(self):
        """ prüft, ob der Ladepunkt vom Benutzer konfiguriert wurde.
        """
        pass

    def __is_cp_available(self):
        """ prüft, ob sich der LP in der vorgegebenen Zeit zurückgemeldet hat.
        """
        pass

    def __is_ev_plugged(self):
        """prüft, ob ein EV angesteckt ist.
        """
        pass

    def __is_cp_locked(self):
        """prüft, ob der LP gesperrt ist
        """
        pass

    def __is_autolock_active(self):
        """ prüft, ob ein Zeitfenster des Autolocks aktiv ist.
        """
        pass

    def get_state(self):
        """prüft alle Bedingungen und ruft die EV-Logik auf
        """
        if __is_cp_configured()==True:
            if __is_cp_available()==True:
                if __is_ev_plugged()==True:
                    if __is_cp_locked()==True:
                        if __is_autolock_active()==True:
        return


class cpTemplate(self):
	""" Vorlage für einen LP.
	"""
	pass
