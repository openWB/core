#!/usr/bin/env python3
from typing import Optional
import logging

from control import data
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.ovum.ovum.config import Ovum

log = logging.getLogger(__name__)


def create_consumer(config: Ovum):
    client = None
    sim_counter = None
    last_mode = 'Undefined'

    def initializer():
        nonlocal client, sim_counter, last_mode
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)
        last_mode = 'Undefined'

    def error_handler() -> None:
        initializer()

    def send_values() -> None:
        # Informativ: aktuellen Netzsaldo in Reg 710 schreiben, damit OVUM-eigene Anzeigen
        # (PV-Watch Messwert Reg 456, Autarkiegrad Reg 450) auch im externen Leistungsvorgabe-
        # Modus (Reg 709 = 2) einen sinnvollen Wert zeigen. UNVERIFIZIERT, ob Reg 710 dabei
        # tatsächlich nur angezeigt und nicht doch in interne Berechnungen einfließt - vor
        # Dauerbetrieb an echter Hardware prüfen, ob Reg 708 dadurch vom 711-Sollwert abweicht.
        grid_power = data.data.counter_all_data.get_evu_counter().data.get.power
        client.write_register(710, int(grid_power / 10), ModbusDataType.INT_16,
                              unit=config.configuration.modbus_id)

    def update() -> ConsumerState:
        # Reg 708: elektrische Leistungsaufnahme Wärmepumpe [kW]*100 -> Watt = Rohwert * 10
        power = client.read_holding_registers(708, ModbusDataType.INT_16,
                                              unit=config.configuration.modbus_id) * 10
        imported, exported = sim_counter.sim_count(power)

        if config.configuration.send_values:
            send_values()

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_limit(power_limit: Optional[float]) -> None:
        nonlocal last_mode
        unit = config.configuration.modbus_id

        if power_limit is None:
            # Keine Leistungsvorgabe gefordert, Ovum-eigene PV-Watch-Regelung übernimmt wieder
            if last_mode != 'self':
                client.write_register(709, 0, ModbusDataType.INT_16, unit=unit)
                log.debug("Keine Leistungsvorgabe, Ovum-eigene PV-Watch-Regelung aktivieren.")
                last_mode = 'self'
        else:
            # Leistungsvorgabe gefordert: externe Steuerung aktivieren (falls noch nicht aktiv)
            # und den absoluten Ziel-Leistungsbezug in Reg 711 schreiben. power_limit ist bereits
            # von openWB berechnet und berücksichtigt die aktuelle WP-Leistungsaufnahme - bewusst
            # NICHT Reg 710 (PV-Watch TCP, roher Netzsaldo) als Regelgröße verwendet, da das laut
            # evcc-Issue #28372 einen Regelkreis-Konflikt erzeugt (WP-eigene Leistung ist im
            # Saldo bereits enthalten, WP-Regler und openWB-Regler können gegeneinander
            # aufschaukeln).
            if last_mode != 'limited':
                client.write_register(709, 2, ModbusDataType.INT_16, unit=unit)
                log.debug("Leistungsvorgabe gefordert, externe Steuerung (Reg 711) aktivieren.")
                last_mode = 'limited'
            raw_value = int(max(power_limit, 0) / 10)  # W -> [kW]*100
            client.write_register(711, raw_value, ModbusDataType.INT_16, unit=unit)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                set_power_limit=set_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Ovum)
