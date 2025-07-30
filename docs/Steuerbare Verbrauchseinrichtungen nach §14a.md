## Steuerbare Verbrauchseinrichtungen (SteuVE) nach § 14a EnGW

Der Gesetzgeber sieht verschiedene Möglichkeiten für steuerbare Verbrauchseinrichtungen vor. Für jede steuerbare Verbrauchseinrichtung kann eine andere Option angemeldet werden. Bei der Konfiguration muss deshalb auch immer der/die Ladepunkte angegeben werden, für die die IO-Aktion angewendet werden soll.

### Dimmen per EMS

Beim Dimmen wird eine maximale Bezugsleistung für alle steuerbaren Verbrauchseinrichtungen nach einer vorgegebene Formel ermittelt. Das Ergebnis dieser Formel muss bei der IO-Aktion `Dimmen` in der Einstellung `maximale Bezugsleistung` eingetragen werden. ACHTUNG: Die openWB kann aktuell nur die Ladepunkte berücksichtigen. Sind noch weitere steuerbare Verbraucher angemeldet, können diese über einen digitalen Ausgang angebunden werden. Da openWB die Leistung dieser Geräte nicht kennt, werden 4,2kW angenommen. Muss der Verbraucher seine Leistung begrenzen, wird der Ausgang auf 0V gesetzt. Für die korrekte Ermittlung der maximalen Bezugsleistung ist der Betreiber, nicht openWB oder die software2 verantwortlich.
Vorhandener Überschuss kann zusätzlich zur maximalen Bezugsleistung verwendet werden.

### Dimmung per Direkt-Steuerung

Bei der Dimmung per Direkt-Steuerung wird jede steuerbare Verbrauchseinrichtung separat angesteuert und ihr Leistungsbezug auf 4,2kW gedimmt.
Pro steuerbarer Verbrauchseinrichtung muss eine IO-Aktion konfiguriert werden und dort der Ladepunkt und der zugehörige Eingang angegeben werden.

### Rundsteuer-Empfänger-Kontakt (RSE)

Für den RSE-Kontakt können Muster aus verschiedenen Eingängen angegeben werden. Es kann frei festgelegt werden, bei welchem Muster die zugeordneten Ladepunkte Gesperrt oder freigegeben sind.

In der abgebildeten Konfiguration werden die Ladepunkte nur freigegeben, wenn beide Kontakte DI1 und DI2 geschlossen sind. Ist auch nur einer geöffnet, wird gesperrt.

![RSE-Beispielkonfiguration](RSE-Beispielkonfiguration.png)

## Steuerbare Erzeugungsanlagen (EZA) nach § 9 EEG

Bitte beachten: Die openWB steuert keinen Wechselrichter an. Sie zeigt lediglich den aktuellen Zustand der Beschränkung an und kann optional das Signal der Eingänge an Ausgänge durchreichen.

Die Einspeise- oder Erzeugungsleistung der EZA (abhängig von der Implementierung in der EZA) wird über drei potentialfreie Signalkontakte der FNN-Steuerbox geregelt. Die openWB übernimmt dabei keine direkte Steuerung des Wechselrichters, sondern visualisiert lediglich und protokolliert den aktuellen Steuerzustand.

Das Signalkabel der FNN-Steuerbox muss daher beispielsweise über ein Koppelrelais mit zwei separaten Schließer-/Wechselkontakten mit dem I/O-Modul der openWB und der Erzeugungsanlage verbunden werden. Falls dies nicht möglich ist, kann die Steuerbox über einfache Koppelrelais mit dem I/O-Modul der openWB verbunden werden und das empfangene Signal an vorhandene Ausgänge des I/O-Moduls (falls vorhanden) durchgereicht werden.

Die Signalkontakte bilden folgende Zustände ab:
S1 -> 60% der EZA
S2 -> 30% der EZA
W3 -> 0% der EZA
alle Kontakte offen -> 100% der EZA

Die Eingangsmuster sind so zu konfigurieren, dass auch bei mehreren geschlossenen Kontakten eine eindeutige Funktion gewährleistet wird. In der abgebildeten Konfiguration hat z.B. der Eingang DI5 für Begrenzung auf 0% Priorität, sodass dieses Muster auch erkannt wird, falls noch einer der Eingänge DI3 oder DI4 geschlossen sind.

![EZA-Beispielkonfiguration](EZA-Beispielkonfiguration.png)
