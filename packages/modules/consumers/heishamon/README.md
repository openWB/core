# Panasonic-Wärmepumpe über HeishaMon

Rein lesender Verbraucher (`METER_ONLY`) über die lokale HTTP-Schnittstelle
`GET http://<IP oder Hostname>/json`. Es wird keine Verbindung zu einem
HeishaMon-MQTT-Broker benötigt. Das Modul schreibt keine Wärmepumpenparameter.

## Konfiguration

```json
{
  "ip_address": "heishamon.local",
  "read_temperatures": true
}
```

`ip_address`: IP-Adresse oder Hostname, ohne Protokoll und ohne `/json`.

`read_temperatures`: optional, standardmäßig `true`. Mit `false` nur die
elektrische Leistung auslesen.

Die passende Einstellungsseite mit Host-Eingabe und Temperatur-Schalter wird im
separaten Repository openwb-ui-settings ergänzt:
https://github.com/kevinwieland/openwb-ui-settings/tree/feat/heishamon-consumer

Bis diese Einstellungsseite in der installierten UI-Version enthalten ist,
ist die Konfiguration über den generischen JSON-Editor bearbeitbar.

## Messwerte

Das Modul sucht in der `heatpump`-Liste anhand von `Name`:

| openWB-Messwert | HeishaMon-Name | Einheit |
| --- | --- | --- |
| Leistung | `Heat_Power_Consumption` | W |
| Temperatur 1: Rücklauf | `Main_Inlet_Temp` | °C |
| Temperatur 2: Vorlauf | `Main_Outlet_Temp` | °C |
| Temperatur 3: Solltemperatur | `Main_Target_Temp` | °C |

Die Temperaturreihenfolge bleibt unverändert. Fehlende, nicht numerische,
nicht endliche oder außerhalb von -50 bis +100 °C liegende Temperaturen werden
als `null` im jeweiligen Listenplatz geliefert. Damit werden beispielsweise
unbelegte Sensorwerte wie -128 oder -78 °C nicht als reale Temperaturen angezeigt.
Die Leistungsmessung funktioniert auch ohne Temperaturen.

Fehlende, negative oder ungültige Leistung löst einen Modulfehler aus.
Echte `0 W` ist gültig. HTTP- und JSON-Fehler werden an die zentrale
openWB-Fehlerbehandlung weitergegeben. Eine Anfrage pro Aktualisierung, Timeout
fünf Sekunden.

## Grenzen

- Ausschließlich `Heat_Power_Consumption` wird ausgewertet. Keine Addition von
  Warmwasser-/Kühlleistung und keine Verwendung thermischer Produktionswerte.
- Modelle/Firmware mit ausschließlich erweiterten Leistungswerten
  (`Heat_Power_Consumption_Extra`) sind nicht abgedeckt. Beispielsweise wird
  ein alter ungültiger Wert von -200 W als Fehler gemeldet, nicht als null.
- Im Kühl- oder Warmwasserbetrieb ist der angezeigte Wert weiterhin exakt
  `Heat_Power_Consumption`, nicht zwingend der Gesamtverbrauch der Wärmepumpe.
- Keine erfundenen Phasenströme aus dem Verdichterstrom.
- Der Energiezähler wird durch openWB aus der Leistung integriert; kein
  echter Stromzählerstand aus der Wärmepumpe. Messauflösung und Einbeziehung
  von Standby, Pumpen oder Heizstab hängen von der Wärmepumpe ab.
- Für die Temperaturdarstellung gilt die obige Reihenfolge; die bestehende
  Oberfläche kann die Werte als generische Temperaturkanäle darstellen.
- Automatisierte Tests basieren auf einer bereitgestellten Geräteantwort.
  Die Installation auf einer openWB erfolgt separat durch den Anwender.

HeishaMon-Schnittstelle und Feldbeschreibung:
https://github.com/heishamon/HeishaMon
