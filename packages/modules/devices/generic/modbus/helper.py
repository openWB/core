def check_data(wert):
    if (wert.reg_type is None or
        wert.byteorder is None or
            wert.wordorder is None):
        raise ValueError(
            f"Unvollständige Konfiguration für Universeller-Modbus: Register-Adresse {wert.reg_address}")
