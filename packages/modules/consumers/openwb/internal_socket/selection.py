"""Validate that each physical openWB socket belongs to one consumer."""
from helpermodules.subdata import SubData


def socket_host(configuration):
    chargepoint_id = getattr(configuration, "chargepoint_id", None)
    if chargepoint_id is None:
        return "localhost"
    cp = SubData.cp_data.get(f"cp{chargepoint_id}")
    if cp is None:
        raise ValueError("Bitte einen vorhandenen openWB-Ladepunkt auswählen.")
    setup = cp.chargepoint.chargepoint_module.config
    if setup.type == "internal_openwb":
        return "localhost"
    if setup.type == "external_openwb":
        host = setup.configuration.ip_address
        if host and host not in ("localhost", "127.0.0.1", "::1"):
            return host
    raise ValueError("Bitte einen internen oder Secondary-openWB-Ladepunkt mit gültiger IP auswählen.")


def validate_selection(configuration, consumer_id=None):
    host = socket_host(configuration)
    for consumer in SubData.consumer_data.values():
        module = consumer.data.module
        if consumer.num == consumer_id or getattr(module, "type", None) != "internal_socket":
            continue
        if socket_host(module.configuration) == host:
            raise ValueError("Die Steckdose dieser openWB kann nur einem Verbraucher zugeordnet werden.")
    return host
