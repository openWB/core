#!/usr/bin/env python3
from typing import Optional
import logging

from modules.common.abstract_consumer import CurrentValues
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.ovum.ovum.config import Ovum

log = logging.getLogger(__name__)


def create_consumer(config: Ovum):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def send_values(values: CurrentValues) -> None:
        # ConsumerUsage.SELF_CONTROLLED: aktiviert Ovum-eigene PV-Watch-Regelung (Reg 709 = 0)
        # und schreibt informativ den aktuellen Netzsaldo in Reg 710, damit OVUM-eigene
        # Anzeigen (PV-Watch Messwert Reg 456, Autarkiegrad Reg 450) einen sinnvollen Wert
        # zeigen. UNVERIFIZIERT, ob Reg 710 dabei tatsächlich nur angezeigt und nicht doch in
        # interne Berechnungen einfließt - vor Dauerbetrieb an echter Hardware prüfen, ob
        # Reg 708 dadurch vom erwarteten Eigenregelungs-Verhalten abweicht. Vor jedem Schreiben
        # wird der Ist-Zustand gelesen, damit unnötige Moduswechsel-Befehle vermieden werden.
        unit = config.configuration.modbus_id

        mode = client.read_holding_registers(709, ModbusDataType.INT_16, unit=unit)
        if mode != 0:
            client.write_register(709, 0, ModbusDataType.INT_16, unit=unit)
            log.debug("Wärmepumpe in Eigenregelung, Ovum-eigene PV-Watch-Regelung aktivieren.")
        client.write_register(710, int(values.evu_power / 10), ModbusDataType.INT_16, unit=unit)

    def update() -> ConsumerState:
        # Reg 708: elektrische Leistungsaufnahme Wärmepumpe [kW]*100 -> Watt = Rohwert * 10
        power = client.read_holding_registers(708, ModbusDataType.INT_16,
                                              unit=config.configuration.modbus_id) * 10
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # ConsumerUsage.SUSPENDABLE_TUNABLE: externe Leistungsvorgabe. Ist-Modus wird vor dem
        # Schreiben gelesen, um unnötige Moduswechsel-Befehle zu vermeiden.
        unit = config.configuration.modbus_id
        mode = client.read_holding_registers(709, ModbusDataType.INT_16, unit=unit)

        if power_limit is None:
            # Keine Leistungsvorgabe gefordert, Ovum-eigene PV-Watch-Regelung übernimmt wieder
            if mode != 0:
                client.write_register(709, 0, ModbusDataType.INT_16, unit=unit)
                log.debug("Keine Leistungsvorgabe, Ovum-eigene PV-Watch-Regelung aktivieren.")
        else:
            # Leistungsvorgabe gefordert: externe Steuerung aktivieren (falls noch nicht aktiv)
            # und den absoluten Ziel-Leistungsbezug in Reg 711 schreiben. power_limit ist bereits
            # von openWB berechnet und berücksichtigt die aktuelle WP-Leistungsaufnahme - bewusst
            # NICHT Reg 710 (PV-Watch TCP, roher Netzsaldo) als Regelgröße verwendet, da das laut
            # evcc-Issue #28372 einen Regelkreis-Konflikt erzeugt (WP-eigene Leistung ist im
            # Saldo bereits enthalten, WP-Regler und openWB-Regler können gegeneinander
            # aufschaukeln).
            if mode != 2:
                client.write_register(709, 2, ModbusDataType.INT_16, unit=unit)
                log.debug("Leistungsvorgabe gefordert, externe Steuerung (Reg 711) aktivieren.")
            raw_value = int(max(power_limit, 0) / 10)  # W -> [kW]*100
            client.write_register(711, raw_value, ModbusDataType.INT_16, unit=unit)

    def switch_on() -> None:
        # ConsumerUsage.SUSPENDABLE_ONOFF: SG-Ready "Empfehlung" (Kontakt 1 = 0, Kontakt 2 = 1) -
        # die WP darf eigene Prioritäten (Legionellenschutz, Mindestlaufzeiten) weiter
        # berücksichtigen, wird aber zum Einschalten angeregt. Ist-Zustand wird vor jedem
        # Schreiben gelesen, um unnötige Befehle zu vermeiden.
        unit = config.configuration.modbus_id

        sg_ready_mode = client.read_holding_registers(1250, ModbusDataType.INT_16, unit=unit)
        if sg_ready_mode != 1:
            client.write_register(1250, 1, ModbusDataType.INT_16, unit=unit)  # SG-Ready per TCP

        contact_1 = client.read_holding_registers(1251, ModbusDataType.INT_16, unit=unit)
        if contact_1 != 0:
            client.write_register(1251, 0, ModbusDataType.INT_16, unit=unit)

        contact_2 = client.read_holding_registers(1252, ModbusDataType.INT_16, unit=unit)
        if contact_2 != 1:
            client.write_register(1252, 1, ModbusDataType.INT_16, unit=unit)

    def switch_off() -> None:
        # ConsumerUsage.SUSPENDABLE_ONOFF: SG-Ready Normalbetrieb (Kontakt 1 = 0, Kontakt 2 = 0)
        unit = config.configuration.modbus_id

        sg_ready_mode = client.read_holding_registers(1250, ModbusDataType.INT_16, unit=unit)
        if sg_ready_mode != 1:
            client.write_register(1250, 1, ModbusDataType.INT_16, unit=unit)  # SG-Ready per TCP

        contact_1 = client.read_holding_registers(1251, ModbusDataType.INT_16, unit=unit)
        if contact_1 != 0:
            client.write_register(1251, 0, ModbusDataType.INT_16, unit=unit)

        contact_2 = client.read_holding_registers(1252, ModbusDataType.INT_16, unit=unit)
        if contact_2 != 0:
            client.write_register(1252, 0, ModbusDataType.INT_16, unit=unit)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                send_values=send_values,
                                set_power_limit=set_power_limit,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Ovum)
