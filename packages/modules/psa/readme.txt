Solange die Konfiguration über UI/JSON nicht funktioniert, siehe https://openwb.de/forum/viewtopic.php?p=75140#p75140
zum Test in config.py die Daten fest eintragen.

                 userid: Optional[str] = "uid",
                 password: Optional[str] = "pwd",
                 client_id: Optional[str] = "clid",
                 client_secret: Optional[str] = "clsc",
                 manufacturer: Optional[str] = "Peugeot",
                 soccalc: Optional[str] = "0",
                 vin: Optional[str] = "PSA1234"):
soccalc und vin werden nicht benutzt.

Alternativ in MQTT das entsprechende Topic schreiben:
openWB/vehicle/<vehicle-id>/soc_module/config
bzw.
openWB/set/vehicle/<vehicle-id>/soc_module/config
