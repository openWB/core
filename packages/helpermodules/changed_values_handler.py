from dataclasses import asdict, fields, is_dataclass
from enum import Enum
import logging
import threading
from typing import Dict, List, Tuple
from control import data

from control.data import Data
from helpermodules.pub import Pub


log = logging.getLogger(__name__)


# In den Metadaten wird unter dem Key der Topic-Suffix ab "openWB/ev/2/" angegeben. Der Topic-Prefix ("openWB/ev/2/")
# wird automatisch ermittelt.
# Der Key mutable_by_algorithm ist True, wenn die Werte im Algorithmus geändert werden können. Nur diese Werte werden
# automatisiert gepublished. Werte, die an anderer Stelle gepublished werden, wie zB Zählerstände, werden mit False
# gekennzeichnet. Um eine Dokumentation der Topics zu erhalten, sollten die Metadaten dennoch ausgefüllt werden.
# Metadaten werden nur für Felder erzeugt, die gepublished werden sollen, dh bei ganzen Klassen für das Feld der
# jeweiligen Klasse. Wenn Werte aus einer instanziierten Klasse gepublished werden sollen, erhält die übergeordnete
# Klasse keine Metadaten (siehe Beispiel unten).
# Damit die geänderten Werte automatisiert gepublished werden können, muss jede Klasse eine bestimmte Form haben:
#
# @dataclass
# class SampleClass:
#     parameter1: bool = False
#     parameter2: int = 5


# def sample_class() -> SampleClass:
#     return SampleClass()


# @dataclass
# class SampleNested:
#     parameter1: bool = field(default=False, metadata={"topic": "get/nested1", "mutable_by_algorithm": True})
#     parameter2: int = field(default=0, metadata={"topic": "get/nested2", "mutable_by_algorithm": True})


# def sample_nested() -> SampleNested:
#     return SampleNested()


# @dataclass
# class SampleData:
#     # Wenn eine ganze Klasse als Dictionary gepublished werden soll, wie zB bei Konfigurationen, werden Metadaten für
# diese Klasse eingetragen. Die Felder der Konfigurationsklasse bekommen keine Metadaten, da diese nicht einzeln
# gepublished werden.
#     sample_field_class: SampleClass = field(
#         default_factory=sample_class, metadata={"topic": "get/field_class", "mutable_by_algorithm": True})
#     sample_field_int: int = field(default=0, metadata={"topic": "get/field_int", "mutable_by_algorithm": True})
#     sample_field_immutable: float = field(
#         default=0, metadata={"topic": "get/field_immutable", "mutable_by_algorithm": False})
#     sample_field_list: List = field(default_factory=currents_list_factory, metadata={
#                                     "topic": "get/field_list", "mutable_by_algorithm": True})
#     # Bei verschachtelten Klassen, wo der zu publishende Wert auf einer tieferen Ebene liegt, werden nur für den zu
# publishenden Wert Metadaten erzeugt.
#     sample_field_nested: SampleNested = field(default_factory=sample_nested)


# class Sample:
#     def __init__(self) -> None:
#         self.data = SampleData()


class ChangedValuesHandler:
    def __init__(self, event_module_update_completed: threading.Event) -> None:
        self.prev_data: Data = Data(event_module_update_completed)

    def store_inital_values(self):
        try:
            # speichern der Daten zum Zyklus-Beginn, um später die geänderten Werte zu ermitteln
            self.prev_data.copy_data()
        except Exception as e:
            log.exception(e)

    def pub_changed_values(self):
        try:
            # publishen der geänderten Werte
            self._update_value("openWB/set/bat/", self.prev_data.bat_all_data.data.get, data.data.bat_all_data.data.get)
            for key, value in data.data.cp_data.items():
                try:
                    self._update_value(f"openWB/set/chargepoint/{value.num}/",
                                       self.prev_data.cp_data[key].data, value.data)
                except Exception as e:
                    log.exception(e)
        except Exception as e:
            log.exception(e)

    def _update_value(self, topic_prefix, data_inst_previous, data_inst):
        for f in fields(data_inst):
            try:
                changed = False
                value = getattr(data_inst, f.name)
                if isinstance(value, Enum):
                    value = value.value
                previous_value = getattr(data_inst_previous, f.name)
                if isinstance(previous_value, Enum):
                    previous_value = previous_value.value
                if hasattr(f, "metadata"):
                    if f.metadata.get("mutable_by_algorithm"):
                        if isinstance(value, (str, int, float, Dict, List, Tuple)):
                            if previous_value != value:
                                changed = True
                        elif isinstance(value, (bool, type(None))):
                            if previous_value is not value:
                                changed = True
                        else:
                            dict_prev = dict(asdict(previous_value))
                            dict_current = dict(asdict(value))
                            if dict_prev != dict_current:
                                changed = True
                                value = asdict(value)
                                previous_value = asdict(previous_value)

                        if changed:
                            topic = f"{topic_prefix}{f.metadata['topic']}"
                            Pub().pub(topic, value)
                            log.debug(f"Topic {topic}, Payload {value}, vorherige Payload: {previous_value}")
                        continue
                if is_dataclass(value):
                    self._update_value(topic_prefix, previous_value, value)
            except Exception as e:
                log.exception(e)
