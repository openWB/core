from dataclasses import dataclass, field
import logging

from control import data


log = logging.getLogger(__name__)


@dataclass
class AllGet:
    daily_imported: float = field(default=0, metadata={"topic": "get/daily_imported"})
    daily_exported: float = field(default=0, metadata={"topic": "get/daily_exported"})
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
        imported, exported, power = 0, 0, 0
        try:
            for consumer in data.data.consumer_data.values():
                try:
                    imported = imported + consumer.data.get.imported
                    exported = exported + consumer.data.get.exported
                except Exception:
                    log.exception("Fehler in der allgemeinen Verbaucher-Klasse für Verbaucher "+consumer)
                try:
                    power = power + consumer.data.get.power
                except Exception:
                    log.exception("Fehler in der allgemeinen Verbaucher-Klasse für Verbaucher "+consumer)
            self.data.get.power = power
            self.data.get.imported = imported
            self.data.get.exported = exported
        except Exception:
            log.exception("Fehler in der allgemeinen Verbaucher-Klasse")
