from dataclasses import dataclass, field
import logging

from control import data
from control.chargepoint.chargepoint_state import ChargepointState
from helpermodules.pub import Pub


log = logging.getLogger(__name__)


@dataclass
class AllGet:
    daily_imported: float = 0
    daily_exported: float = 0
    power: float = 0
    imported: float = 0
    exported: float = 0


def all_get_factory() -> AllGet:
    return AllGet()


@dataclass
class AllChargepointData:
    get: AllGet = field(default_factory=all_get_factory)


def all_chargepoint_data_factory() -> AllChargepointData:
    return AllChargepointData()


@dataclass
class AllChargepoints:
    data: AllChargepointData = field(default_factory=all_chargepoint_data_factory)

    def no_charge(self):
        """ Wenn keine EV angesteckt sind oder keine Verzögerungen aktiv sind, werden die Algorithmus-Werte
        zurückgesetzt.
        (dient der Robustheit)
        """
        try:
            for cp in data.data.cp_data:
                try:
                    chargepoint = data.data.cp_data[cp]
                    # Kein EV angesteckt
                    control_parameter = chargepoint.data.control_parameter
                    if (not chargepoint.data.get.plug_state or
                            # Kein EV, das Laden soll
                            chargepoint.data.set.charging_ev == -1 or
                            # Kein EV, das auf das Ablaufen der Einschalt- oder Phasenumschaltverzögerung wartet
                            (chargepoint.data.set.charging_ev != -1 and
                                control_parameter.state != ChargepointState.PERFORMING_PHASE_SWITCH and
                                control_parameter.state != ChargepointState.PHASE_SWITCH_DELAY and
                                control_parameter.state != ChargepointState.SWITCH_OFF_DELAY and
                                control_parameter.state != ChargepointState.SWITCH_ON_DELAY)):
                        continue
                    else:
                        break
                except Exception:
                    log.exception("Fehler in der allgemeinen Ladepunkt-Klasse für Ladepunkt "+cp)
            else:
                data.data.counter_all_data.get_evu_counter().reset_pv_data()
        except Exception:
            log.exception("Fehler in der allgemeinen Ladepunkt-Klasse")

    def get_cp_sum(self):
        """ ermittelt die aktuelle Leistung und Zählerstand von allen Ladepunkten.
        """
        imported, exported, power = 0, 0, 0
        try:
            for cp in data.data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        power = power + chargepoint.data.get.power
                        imported = imported + chargepoint.data.get.imported
                        exported = exported + chargepoint.data.get.exported
                except Exception:
                    log.exception("Fehler in der allgemeinen Ladepunkt-Klasse für Ladepunkt "+cp)
            self.data.get.power = power
            Pub().pub("openWB/set/chargepoint/get/power", power)
            self.data.get.imported = imported
            Pub().pub("openWB/set/chargepoint/get/imported", imported)
            self.data.get.exported = exported
            Pub().pub("openWB/set/chargepoint/get/exported", exported)
        except Exception:
            log.exception("Fehler in der allgemeinen Ladepunkt-Klasse")
