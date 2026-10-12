from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import json
import logging
from helpermodules.utils.precision_math import (decimal_add,
                                                decimal_subtract,
                                                decimal_multiply)

from helpermodules.messaging import MessageType, pub_system_message

log = logging.getLogger(__name__)


class CalculationType(Enum):
    ALL = 0
    POWER = 1
    ENERGY = 2


FILE_ERRORS = (FileNotFoundError, json.decoder.JSONDecodeError)


def safe_get_nested(data: Dict, *keys, default: Union[int, float] = 0) -> Union[int, float]:
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current if isinstance(current, (int, float)) else default


def get_totals(entries: List, process_entries: bool = True) -> Dict:
    """ Berechnet aus der übergebenen Liste "entries" die Summen (totals).
        "process_entries" besagt, ob die Differenzen der einzelnen Einträge noch
        berechnet werden müssen.
    """
    if process_entries:
        entries = _process_entries(entries, CalculationType.ENERGY)
    totals = {"consumer": {}, "cp": {}, "counter": {}, "pv": {}, "bat": {}, "sh": {}, "hc": {}}
    for totals_group in totals.keys():
        for entry in entries:
            if totals_group in entry:
                for entry_module in entry[totals_group]:
                    try:
                        if entry_module not in totals[totals_group]:
                            if totals_group == "hc":
                                totals[totals_group][entry_module] = {"energy_imported": 0.0}
                            elif totals_group == "pv":
                                totals[totals_group][entry_module] = {"energy_exported": 0.0}
                            else:
                                totals[totals_group][entry_module] = {"energy_imported": 0.0, "energy_exported": 0.0}
                                if totals_group == "counter" and "grid" in entry[totals_group][entry_module]:
                                    totals[totals_group][entry_module]["grid"] = entry[
                                        totals_group][entry_module]["grid"]
                        for entry_module_key, entry_module_value in entry[totals_group][entry_module].items():
                            if "grid" != entry_module_key and entry_module_key in totals[totals_group][entry_module]:
                                # avoid floating point issues with using Decimal
                                current_total = totals[totals_group][entry_module][entry_module_key]
                                totals[totals_group][entry_module][entry_module_key] = decimal_add(
                                    current_total, entry_module_value)  # totals in Wh!

                    except Exception:
                        log.exception(f"Fehler beim Berechnen der Summe von {entry_module}; "
                                      f"group:{totals_group}, module:{entry_module}, key:{entry_module_key}")
    return totals


def _process_entries(entries: List, calculation: CalculationType):
    if entries:
        if len(entries) == 1:
            # Wenn es nur einen Eintrag gibt, kann keine Differenz berechnet werden und die Werte sind 0.
            entry = entries[0]
            for type in ("bat", "consumer", "counter", "cp", "pv", "sh", "hc"):
                if type in entry:
                    for module in entry[type].keys():
                        if calculation in [CalculationType.POWER, CalculationType.ALL]:
                            entry[type][module].update({
                                "power_average": 0,
                                "power_imported": 0,
                                "power_exported": 0
                            })
                        if calculation in [CalculationType.ENERGY, CalculationType.ALL]:
                            entry[type][module].update({
                                "energy_imported": 0,
                                "energy_exported": 0
                            })
        elif len(entries) > 1:
            for i in range(0, len(entries)-1):
                entry = entries[i]
                next_entry = entries[i+1]
                entries[i] = process_entry(entry, next_entry, calculation)
            entries.pop()
    return entries


def process_entry(entry: dict, next_entry: dict, calculation: CalculationType):
    time_diff = next_entry["timestamp"] - entry["timestamp"]
    for type in ("bat", "consumer", "counter", "cp", "pv", "sh", "hc"):
        if type in entry:
            for module in entry[type].keys():
                try:
                    new_data = {}
                    if "imported" in entry[type][module].keys() or "exported" in entry[type][module].keys():
                        def get_current_and_next(value_key: str) -> Tuple[float, float]:
                            def get_single_value(source: dict) -> Optional[float]:
                                try:
                                    value = source[type][module][value_key]
                                    if isinstance(value, (int, float)):
                                        return float(value)
                                except KeyError:
                                    pass
                                return None

                            current_value = get_single_value(entry)
                            next_value = get_single_value(next_entry)

                            # Keep meter deltas neutral if one side is invalid/missing.
                            if current_value is None and next_value is None:
                                return 0.0, 0.0
                            if current_value is None:
                                return next_value, next_value
                            if next_value is None:
                                return current_value, current_value
                            return current_value, next_value
                        value_imported, next_value_imported = get_current_and_next("imported")
                        value_exported, next_value_exported = get_current_and_next("exported")
                        if calculation in [CalculationType.POWER, CalculationType.ALL]:
                            if next_value_imported < value_imported or next_value_exported < value_exported:
                                # do not calculate as we have a backwards jump in our meter value!
                                average_power = 0
                            else:
                                average_power = _calculate_average_power(
                                    time_diff, value_imported, next_value_imported,
                                    value_exported, next_value_exported)
                            new_data.update({
                                "power_average": average_power,
                                "power_imported": average_power if average_power >= 0 else 0,
                                "power_exported": average_power * -1 if average_power < 0 else 0
                            })
                        if calculation in [CalculationType.ENERGY, CalculationType.ALL]:
                            if next_value_imported < value_imported:
                                # do not calculate as we have a backwards jump in our meter value!
                                energy_imported = 0
                            else:
                                energy_imported = decimal_subtract(next_value_imported,
                                                                   value_imported)
                            if next_value_exported < value_exported:
                                # do not calculate as we have a backwards jump in our meter value!
                                energy_exported = 0
                            else:
                                energy_exported = decimal_subtract(next_value_exported,
                                                                   value_exported)
                            new_data.update({
                                "energy_imported": energy_imported,
                                "energy_exported": energy_exported
                            })
                    entry[type][module].update(new_data)
                except Exception:
                    log.exception("Fehler beim Berechnen der Leistung")
            # next_entry may contain new modules, we add them here
            try:
                for module, module_data in next_entry[type].items():
                    if module not in entry[type].keys():
                        log.debug(f"adding module {module} from next entry")
                        if calculation in [CalculationType.POWER, CalculationType.ALL]:
                            module_data.update({"power_average": 0, "power_imported": 0, "power_exported": 0})
                        if calculation in [CalculationType.ENERGY, CalculationType.ALL]:
                            module_data.update({"energy_imported": 0, "energy_exported": 0})
                        entry[type].update({module: module_data})
            except KeyError:
                # catch missing "type"
                pass
    return entry


def _calculate_average_power(time_diff: float, current_imported: float = 0, next_imported: float = 0,
                             current_exported: float = 0, next_exported: float = 0) -> float:
    imported_diff = decimal_subtract(next_imported, current_imported)
    exported_diff = decimal_subtract(next_exported, current_exported)
    energy_diff = decimal_subtract(imported_diff, exported_diff)
    return decimal_multiply(energy_diff, 3600 / time_diff)  # Ws -> W


def analyse_percentage(entry) -> Tuple[Dict, str]:
    EOOR_STATE_MSG = ("Der Strom-Mix um " + entry["date"] +
                      " konnte nicht berechnet werden, da sich {} im Fehlerzustand befindet. Alle Verbräuche werden" +
                      " dem Netz zugerechnet.\n")

    def format(value):
        return round(value, 4)

    def get_grid_counter(entry) -> Dict:
        # es gibt nur einen Zähler am EVU-Punkt
        for counter in entry["counter"].values():
            if counter.get("grid") is True:
                return counter
        else:
            raise KeyError(f"Kein Zähler für das Netz gefunden in Eintrag '{entry['timestamp']}'.")
    try:
        message = ""
        grid_counter = get_grid_counter(entry)
        # Wenn neben dem "all" Eintrag kein weiterer Eintrag existiert, dann gibt es keine Komponenten.
        if ((safe_get_nested(entry, "bat", "all", "fault_state") == 2 and len(entry.get("bat", {})) > 1) or
                (safe_get_nested(entry, "cp", "all", "fault_state") == 2 and len(entry.get("cp", {})) > 1) or
                (safe_get_nested(entry, "pv", "all", "fault_state") == 2 and len(entry.get("pv", {})) > 1) or
                grid_counter.get("fault_state", None) == 2):

            entry["energy_source"] = {"grid": 1, "pv": 0, "bat": 0, "cp": 0}
            if safe_get_nested(entry, "bat", "all", "fault_state") == 2 and len(entry.get("bat", {})) > 1:
                message += EOOR_STATE_MSG.format("mind. einer der Speicher")
            if safe_get_nested(entry, "cp", "all", "fault_state") == 2 and len(entry.get("cp", {})) > 1:
                message += EOOR_STATE_MSG.format("mind. einer der Ladepunkte")
            if safe_get_nested(entry, "pv", "all", "fault_state") == 2 and len(entry.get("pv", {})) > 1:
                message += EOOR_STATE_MSG.format("mind. einer der Wechselrichter")
            if grid_counter.get("fault_state", None) == 2:
                message += EOOR_STATE_MSG.format("der Zähler für das Netz")

        else:
            bat_imported = safe_get_nested(entry, "bat", "all", "energy_imported")
            bat_exported = safe_get_nested(entry, "bat", "all", "energy_exported")
            cp_exported = safe_get_nested(entry, "cp", "all", "energy_exported")
            pv_exported = safe_get_nested(entry, "pv", "all", "energy_exported")
            grid_imported = grid_counter.get("energy_imported", 0)
            grid_exported = grid_counter.get("energy_exported", 0)
            consumption = grid_imported - grid_exported + pv_exported + bat_exported - bat_imported + cp_exported
            if consumption < 0:
                consumption = 0

            try:
                # Berechnung der Energiequellenanteile:
                # Da die genaue Aufteilung der Energiequellen nicht bekannt ist,
                # wird die Einspeisung (grid_exported) entsprechend der folgenden Priorität aufgeteilt:
                #     1. PV
                #     2. Batterie
                #     3. CP
                # Sollte die Einspeisung nicht komplett von PV gedeckt werden,
                # wird der Rest von der Batterie übernommen, und falls nötig, vom CP.
                #
                # Entsprechend ähnlich wird der Batterieimport nach folgender Priorität aufgeteilt:
                #     1. PV
                #     2. Grid
                #     3. CP
                #
                # Anschließend wird der Verbrauch (ohne Einspeisung und Batterieimport) auf energy_source aufgeteilt.
                if consumption <= 0:
                    entry["energy_source"] = {"grid": 0, "pv": 0, "bat": 0, "cp": 0}
                else:

                    direct = {"grid": grid_imported, "pv": pv_exported, "bat": bat_exported, "cp": cp_exported}

                    # Einspeißung aufteilen
                    unassigned_export = grid_exported
                    for source in ("pv", "bat", "cp"):
                        if direct[source] > unassigned_export:
                            direct[source] -= unassigned_export
                            unassigned_export = 0
                            break
                        else:
                            unassigned_export -= direct[source]
                            direct[source] = 0

                    if unassigned_export > 0:
                        # Fehler / inkonsistente Energiebilanz
                        log.warning(
                            f"grid_exported konnte nicht vollständig verteilt werden. "
                            f"Unverteilter Anteil: {unassigned_export}"
                        )

                    # Batterieimport aufteilen
                    unassigned_bat_import = bat_imported
                    for source in ("pv", "grid", "cp"):
                        if direct[source] > unassigned_bat_import:
                            direct[source] -= unassigned_bat_import
                            unassigned_bat_import = 0
                            break
                        else:
                            unassigned_bat_import -= direct[source]
                            direct[source] = 0

                    if unassigned_bat_import > 0:
                        # Fehler / inkonsistente Energiebilanz
                        log.warning(
                            f"bat_imported konnte nicht vollständig verteilt werden. "
                            f"Unverteilter Anteil: {unassigned_bat_import}"
                        )

                    # Anschließend Verbrauch aufteilen, wenn vorhanden
                    direct_total = sum(direct.values())

                    if direct_total <= 0:
                        entry["energy_source"] = {"grid": 0, "pv": 0, "bat": 0, "cp": 0}
                    else:
                        entry["energy_source"] = {
                            "grid": format(direct["grid"] / direct_total),
                            "pv": format(direct["pv"] / direct_total),
                            "bat": format(direct["bat"] / direct_total),
                            "cp": format(direct["cp"] / direct_total)}
            except ZeroDivisionError:
                entry["energy_source"] = {"grid": 0, "pv": 0, "bat": 0, "cp": 0}
    except Exception:
        log.exception(f"Fehler beim Berechnen des Strom-Mix von {entry['timestamp']}")
        message += f"Fehler beim Berechnen des Strom-Mix von {entry['timestamp']}.\n"
    finally:
        return entry, message


ERROR_STATE_MESSAGE = ("Die Anteile der Energiequellen für {} konnten nicht berechnet werden, da er sich im " +
                       "Fehlerzustand befindet. Die Verbräuche werden mit 0 kWh angesetzt.\n")


def calc_energy_imported_by_source(entry, names, message_key_filter: Optional[str] = None) -> Tuple[Dict, str]:
    try:
        message = ""

        if "energy_source" in entry.keys():
            energy_source = entry["energy_source"]
            hc_section = entry.get("hc")
            if isinstance(hc_section, dict) and "all" in hc_section:
                hc_all = hc_section["all"]
                if isinstance(hc_all, dict):
                    if hc_all.get("fault_state", 0) != 2 and "energy_imported" in hc_all:
                        for source in ("grid", "pv", "bat", "cp"):
                            hc_all[f"energy_imported_{source}"] = decimal_multiply(
                                hc_all["energy_imported"], energy_source[source])
                    else:
                        for source in ("grid", "pv", "bat", "cp"):
                            hc_all[f"energy_imported_{source}"] = 0
                        if message_key_filter is None or message_key_filter == "hc":
                            message += ERROR_STATE_MESSAGE.format("den Hausverbrauch")

            cp_section = entry.get("cp")
            if isinstance(cp_section, dict):
                for cp_key, cp_data in cp_section.items():
                    if isinstance(cp_data, dict):
                        if cp_data.get("fault_state", 0) != 2 and "energy_imported" in cp_data:
                            for source in ("grid", "pv", "bat", "cp"):
                                cp_data[f"energy_imported_{source}"] = decimal_multiply(
                                    cp_data["energy_imported"], energy_source[source])
                        else:
                            for source in ("grid", "pv", "bat", "cp"):
                                cp_data[f"energy_imported_{source}"] = 0
                            if message_key_filter is None or message_key_filter == cp_key:
                                message += ERROR_STATE_MESSAGE.format(f"Ladepunkt {names.get(cp_key, cp_key)}")

            consumer_section = entry.get("consumer")
            if isinstance(consumer_section, dict):
                for consumer_key, consumer_data in consumer_section.items():
                    if isinstance(consumer_data, dict):
                        if consumer_data.get("fault_state", 0) != 2 and "energy_imported" in consumer_data:
                            for source in ("grid", "pv", "bat", "cp"):
                                consumer_data[f"energy_imported_{source}"] = decimal_multiply(
                                    consumer_data["energy_imported"], energy_source[source])
                        else:
                            for source in ("grid", "pv", "bat", "cp"):
                                consumer_data[f"energy_imported_{source}"] = 0
                            if message_key_filter is None or message_key_filter == consumer_key:
                                message += ERROR_STATE_MESSAGE.format(
                                    f"Verbraucher {names.get(consumer_key, consumer_key)}")

            counter_section = entry.get("counter")
            if isinstance(counter_section, dict):
                for counter_key, counter_data in counter_section.items():
                    if isinstance(counter_data, dict) and counter_data.get("grid") is False:
                        if counter_data.get("fault_state", 0) != 2 and "energy_imported" in counter_data:
                            for source in ("grid", "pv", "bat", "cp"):
                                counter_data[f"energy_imported_{source}"] = decimal_multiply(
                                    counter_data["energy_imported"], energy_source[source])
                        else:
                            for source in ("grid", "pv", "bat", "cp"):
                                counter_data[f"energy_imported_{source}"] = 0
                            if message_key_filter is None or message_key_filter == counter_key:
                                message += ERROR_STATE_MESSAGE.format(f"Zähler {names.get(counter_key, counter_key)}")
    except Exception:
        log.exception(f"Fehler beim Berechnen der Energie-Anteile aus dem Strom-Mix von {entry['timestamp']}")
        message += f"Fehler beim Berechnen des Strom-Mix von {entry['timestamp']}.\n"
    finally:
        return entry, message


def analyse_percentage_totals(entries, totals):
    sources = ("grid", "pv", "bat", "cp")

    def ensure_zero_source_keys(module_totals: Dict):
        if isinstance(module_totals, dict):
            for source in sources:
                module_totals[f"energy_imported_{source}"] = 0
    try:
        for section in ("consumer", "cp", "hc"):
            if "all" not in totals[section].keys():
                totals[section]["all"] = {}
        for source in sources:
            totals["hc"]["all"].update({f"energy_imported_{source}": 0})
            for entry in entries:
                if "hc" in entry.keys() and "all" in entry["hc"].keys():
                    current_value = totals["hc"]["all"][f"energy_imported_{source}"]
                    add_value = entry["hc"]["all"].get(f"energy_imported_{source}", 0)
                    totals["hc"]["all"][f"energy_imported_{source}"] = decimal_add(
                        current_value, add_value)
                for key in entry["cp"].keys():
                    if f"energy_imported_{source}" in entry["cp"][key].keys():
                        if totals["cp"][key].get(f"energy_imported_{source}") is None:
                            totals["cp"][key].update({f"energy_imported_{source}": 0})
                        current_value = totals["cp"][key][f"energy_imported_{source}"]
                        add_value = entry["cp"][key][f"energy_imported_{source}"]
                        totals["cp"][key][f"energy_imported_{source}"] = decimal_add(
                            current_value, add_value)
                for key in entry["consumer"].keys():
                    if f"energy_imported_{source}" in entry["consumer"][key].keys():
                        if totals["consumer"][key].get(f"energy_imported_{source}") is None:
                            totals["consumer"][key].update({f"energy_imported_{source}": 0})
                        current_value = totals["consumer"][key][f"energy_imported_{source}"]
                        add_value = entry["consumer"][key][f"energy_imported_{source}"]
                        totals["consumer"][key][f"energy_imported_{source}"] = decimal_add(
                            current_value, add_value)
                for key, counter in entry["counter"].items():
                    if counter["grid"] is False and f"energy_imported_{source}" in counter:
                        if totals["counter"][key].get(f"energy_imported_{source}") is None:
                            totals["counter"][key].update({f"energy_imported_{source}": 0})
                        current_value = totals["counter"][key][f"energy_imported_{source}"]
                        add_value = counter[f"energy_imported_{source}"]
                        totals["counter"][key][f"energy_imported_{source}"] = decimal_add(
                            current_value, add_value)
    except Exception:
        log.exception("Fehler beim Berechnen der Summen der Energiequellen")
        # Im Fehlerfall werden die Totals auf 0 gesetzt
        # -> dann wird nur die Ladung/Entladung-Leistung angezeigt.
        # -> sprich keine Aufteilung der Energiequellen, sondern nur die Gesamtwerte.
        totals.setdefault("hc", {})
        totals["hc"].setdefault("all", {})
        ensure_zero_source_keys(totals["hc"]["all"])

        totals.setdefault("cp", {})
        for key, module_totals in totals["cp"].items():
            ensure_zero_source_keys(module_totals)

        totals.setdefault("counter", {})
        for key, module_totals in totals["counter"].items():
            ensure_zero_source_keys(module_totals)

        return totals
    return totals


def _analyse_energy_source(data, calc_cp: Optional[str] = None) -> Dict:
    if data and len(data["entries"]) > 0:
        try:
            if data.get("message") is None:
                data["message"] = ""
            for i in range(0, len(data["entries"])):
                data["entries"][i], message_analyse = analyse_percentage(data["entries"][i])
                data["entries"][i], message_calc = calc_energy_imported_by_source(
                    data["entries"][i], data["names"], message_key_filter=calc_cp)
                data["message"] += message_analyse + message_calc
            data["totals"] = analyse_percentage_totals(data["entries"], data["totals"])
        except Exception:
            log.exception("Fehler beim Analysieren der Energiequellen")
            pub_system_message({}, "Fehler beim Berechnen des Strom-Mix", MessageType.ERROR)
            data["message"] = "Fehler beim Berechnen des Strom-Mix."
    return data
