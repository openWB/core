### IO-Geräte
IO/GPIO sind analoge und digitale Ein- und Ausgänge, die man meist als Pin- oder Buchsenleiste auf der Platine findet. openWB software2 kann analoge und digitale Eingänge auslesen und analoge sowie digitale Ausgänge schalten. Die Ein- und Ausgänge befinden sich auf dem konfigurierten IO-Gerät, wie zB dem Dimm- & Control-Kit. Um festzulegen, was mit den Informationen aus den Eingängen gemacht werden soll oder welche Ausgänge geschaltet werden sollen, konfigurierst Du IO-Aktionen. Bei der IO-Aktion gibst Du an, welcher Ein- oder Ausgang dafür verwendet werden soll und ggf weiter Aktions-spezifische Einstellungen.

#### Dimm-& Control-Kit
Das Dimm-& Control-Kit besitzt acht analoge Eingänge (AI1-AI8), acht digitale Eingänge (DI1-DI8) und achte digitale Ausgänge (DO1-DO8). Bei den Ausgängen handelt es sich um potentialfreie Relais-Ausgänge mit 5A@28VDC/250VAC.

#### openWB series2-Modell mit AddOn-Platine
Die AddOn-Platine stellt 7 Eingänge und 3 Ausgänge zur Verfügung. WICHTIG: In openWB software 1.9 waren den IOs feste Aktionen zugeordnet, die auch der Platine beschriftet sind. Diese Zuordnung ist in software2 NICHT vorgegeben. Zur einfachen Zuordnung der Pins hier eine Übersicht:
| Pin | Beschriftung |
|---------|---------|
| Eingang 21 | RSE 2 |
| Eingang 24 | RSE 1 |
| Eingang 31 | Taster 3 PV |
| Eingang 32 | Taster 1 Sofortladen |
| Eingang 33 | Taster 4 Stop |
| Eingang 36 | Taster 2 Min+PV |
| Eingang 40 | Taster 5 Standby |
| Ausgang 7  | LED 3 |
| Ausgang 16 | LED 2 |
| Ausgang 18 | LED 1 |


### IO-Aktionen

#### Steuerbare Verbrauchseinrichtungen: Dimmen, Dimmung per Direkt-Steuerung, RSE
Ausführliche Informationen findest Du im gesonderten Wiki-Beitrag [Steuerbare Verbrauchseinrichtungen](https://github.com/openWB/core/wiki/Steuerbare-Verbrauchseinrichtungen)

Weitere IO-Aktionen sind in Arbeit.