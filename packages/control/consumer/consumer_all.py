from dataclasses import dataclass, field
import logging

from control import data
from helpermodules.constants import NO_ERROR


log = logging.getLogger(__name__)


@dataclass
class AllGet:
    daily_imported: float = field(default=0, metadata={"topic": "get/daily_imported"})
    daily_exported: float = field(default=0, metadata={"topic": "get/daily_exported"})
    fault_str: str = field(default=NO_ERROR, metadata={"topic": "get/fault_str"})
    fault_state: int = field(default=0, metadata={"topic": "get/fault_state"})
    power: float = field(default=0, metadata={"topic": "get/power"})
    imported: float = field(default=0, metadata={"topic": "get/imported"})
    exported: float = field(default=0, metadata={"topic": "get/exported"})


def all_get_factory() -> AllGet:
    return AllGet()


@dataclass
class AllConsumerData:
    get: AllGet = field(default_factory=all_get_factory)


def all_Consumer_data_factory() -> AllConsumerData:
    return AllConsumerData()


@dataclass
class AllConsumers:
    data: AllConsumerData = field(default_factory=all_Consumer_data_factory)

    def get_consumer_sum(self):
        imported, exported, power, fault_state = 0, 0, 0, 0
        try:
            for consumer in data.data.consumer_data.values():
                try:
                    power = power + consumer.data.get.power
                except Exception:
                    log.exception(f"Fehler in der allgemeinen Verbaucher-Klasse für Verbaucher {consumer}")
                imported = imported + consumer.data.get.imported
                exported = exported + consumer.data.get.exported
                fault_state = max(fault_state, consumer.data.get.fault_state)

            self.data.get.power = power
            self.data.get.imported = imported
            self.data.get.exported = exported
            self.data.get.fault_state = fault_state
            self.data.get.fault_str = NO_ERROR if fault_state == 0 else (
                "Bitte die Statusmeldungen der Verbraucher prüfen. "
                "Es haben nicht alle Module aktuelle Zählerstände geliefert.")
        except Exception:
            log.exception("Fehler in der allgemeinen Verbaucher-Klasse")
