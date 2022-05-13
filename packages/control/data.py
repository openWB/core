""" Verschachtelte Listen, die die Daten zur Berechnung des Algorithmus enthalten.
Dictionary: Zugriff erfolgt bei Dictionary über Keys, nicht über Indizes wie bei Listen. Das hat den Vorteil, dass
Instanzen gelöscht werden können, der Zugriff aber nicht verändert werden muss.
"""
import logging
import threading

log = logging.getLogger(__name__)

data = None


class Data:
    def __init__(self):
        self.event = threading.Event()
        self.event.set()
        self._bat_data = {}
        self._bat_module_data = {}
        self._counter_data = {}
        self._counter_module_data = {}
        self._cp_data = {}
        self._cp_template_data = {}
        self._ev_charge_template_data = {}
        self._ev_data = {}
        self._ev_template_data = {}
        self._general_data = {}
        self._graph_data = {}
        self._optional_data = {}
        self._pv_data = {}
        self._system_data = {}

    # getter-Funktion, der Zugriff erfolgt wie bei einem Zugriff auf eine öffentliche Variable.
    @property
    def bat_data(self):
        """ gibt die Variable zurück. Durch das Event wird verhindert, das gleichzeitig geschrieben und gelesen wird.

        Return
        ------
        temp: Variable
        """
        self.event.wait()
        self.event.clear()
        temp = self._bat_data
        self.event.set()
        return temp

    @bat_data.setter
    def bat_data(self, value):
        """ setzt die Variable. Durch das Event wird verhindert, das gleichzeitig geschrieben und gelesen wird.

        Parameter
        ---------
        value: Wert, der gesetzt werden soll.
        """
        self.event.wait()
        self.event.clear()
        self._bat_data = value
        self.event.set()

    @property
    def graph_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._graph_data
        self.event.set()
        return temp

    @graph_data.setter
    def graph_data(self, value):
        self.event.wait()
        self.event.clear()
        self._graph_data = value
        self.event.set()

    @property
    def counter_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._counter_data
        self.event.set()
        return temp

    @counter_data.setter
    def counter_data(self, value):
        self.event.wait()
        self.event.clear()
        self._counter_data = value
        self.event.set()

    @property
    def counter_module_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._counter_module_data
        self.event.set()
        return temp

    @counter_module_data.setter
    def counter_module_data(self, value):
        self.event.wait()
        self.event.clear()
        self._counter_module_data = value
        self.event.set()

    @property
    def cp_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._cp_data
        self.event.set()
        return temp

    @cp_data.setter
    def cp_data(self, value):
        self.event.wait()
        self.event.clear()
        self._cp_data = value
        self.event.set()

    @property
    def cp_template_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._cp_template_data
        self.event.set()
        return temp

    @cp_template_data.setter
    def cp_template_data(self, value):
        self.event.wait()
        self.event.clear()
        self._cp_template_data = value
        self.event.set()

    @property
    def ev_charge_template_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._ev_charge_template_data
        self.event.set()
        return temp

    @ev_charge_template_data.setter
    def ev_charge_template_data(self, value):
        self.event.wait()
        self.event.clear()
        self._ev_charge_template_data = value
        self.event.set()

    @property
    def ev_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._ev_data
        self.event.set()
        return temp

    @ev_data.setter
    def ev_data(self, value):
        self.event.wait()
        self.event.clear()
        self._ev_data = value
        self.event.set()

    @property
    def ev_template_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._ev_template_data
        self.event.set()
        return temp

    @ev_template_data .setter
    def ev_template_data(self, value):
        self.event.wait()
        self.event.clear()
        self._ev_template_data = value
        self.event.set()

    @property
    def general_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._general_data
        self.event.set()
        return temp

    @general_data.setter
    def general_data(self, value):
        self.event.wait()
        self.event.clear()
        self._general_data = value
        self.event.set()

    @property
    def optional_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._optional_data
        self.event.set()
        return temp

    @optional_data.setter
    def optional_data(self, value):
        self.event.wait()
        self.event.clear()
        self._optional_data = value
        self.event.set()

    @property
    def pv_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._pv_data
        self.event.set()
        return temp

    @pv_data.setter
    def pv_data(self, value):
        self.event.wait()
        self.event.clear()
        self._pv_data = value
        self.event.set()

    @property
    def system_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._system_data
        self.event.set()
        return temp

    @system_data.setter
    def system_data(self, value):
        self.event.wait()
        self.event.clear()
        self._system_data = value
        self.event.set()

    def print_all(self):
        self._print_dictionaries(self._bat_data)
        self._print_dictionaries(self._bat_module_data)
        self._print_dictionaries(self._cp_data)
        self._print_dictionaries(self._cp_template_data)
        self._print_dictionaries(self._counter_data)
        self._print_dictionaries(self._counter_module_data)
        self._print_dictionaries(self._ev_charge_template_data)
        self._print_dictionaries(self._ev_data)
        self._print_dictionaries(self._ev_template_data)
        self._print_dictionaries(self._general_data)
        self._print_dictionaries(self._graph_data)
        self._print_dictionaries(self._optional_data)
        self._print_dictionaries(self._pv_data)
        self._print_dictionaries(self._system_data)
        log.debug("\n")

    def _print_dictionaries(self, data):
        """ gibt zu Debug-Zwecken für jeden Key im übergebenen Dictionary das Dictionary aus.

        Parameter
        ---------
        data: dict
        """
        for key in data:
            try:
                if not isinstance(data[key], dict):
                    try:
                        log.debug(key+"\n"+str(data[key].data))
                    except AttributeError:
                        # Devices haben kein data-Dict
                        pass
                else:
                    log.debug(key+"\n"+"Klasse fehlt")
            except Exception:
                log.exception("Fehler im Data-Modul")


def data_init():
    """instanziiert die Data-Klasse.
    """
    global data
    data = Data()
