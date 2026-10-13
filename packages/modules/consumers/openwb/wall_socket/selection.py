"""Resolve socket ownership from the selected chargepoint, never a copied IP."""
from helpermodules.subdata import SubData


def socket_host(configuration):
    chargepoint_id = getattr(configuration, "chargepoint_id", None)
    if chargepoint_id is None:
        return "localhost"
    cp = SubData.cp_data.get(f"cp{chargepoint_id}")
    if cp is None:
        raise ValueError("Bitte einen vorhandenen Secondary-Ladepunkt auswählen.")
    setup = cp.chargepoint.chargepoint_module.config
    host = setup.configuration.ip_address
    if setup.type != "external_openwb" or not host or host in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Bitte einen Secondary-openWB-Ladepunkt mit gültiger IP auswählen.")
    return host


def validate_selection(configuration, consumer_id=None):
    host = socket_host(configuration)
    for consumer in SubData.consumer_data.values():
        module = consumer.data.module
        if consumer.num == consumer_id or getattr(module, "type", None) != "gpio_sdm120":
            continue
        if socket_host(getattr(module, "configuration", None)) == host:
            raise ValueError("Die Steckdose dieser openWB kann nur einem Verbraucher zugeordnet werden.")
    return host
