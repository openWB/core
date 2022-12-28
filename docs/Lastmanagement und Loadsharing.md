Das Lastmanagement steuert die Freigabe des Ladestroms, wenn nicht alle Ladepunkte mit voller Leistung laden könnnen. Begrenzende Faktoren könnnen der Hausanschluss, Sicherungen oder Zuleitungen sein.

Die Priorisierung der Ladepunkte beschreibt der Hilfetext unter _Einstellungen -> Konfiguration -> Fahrzeuge -> Ladeprofil-Vorlage -> \*beliebige Vorlage\* -> Aktiver Lademodus_.
Das Lastmanagement funktioniert dreistufig:
1. Zuteilung des Fahrzeug-Mindeststroms unter Berücksichtigung des Lastmanagements: Der Ladepunkt mit der höchsten Priorisierung erhält zuerst eine Stromzuteilung.
2. Zuteilung des Lademodus-Sollstroms unter Berücksichtigung des Lastmanagements: Der verfügbare Strom wird unter allen Ladepunkten mit der gleichen Priorisierung aufgeteilt.
3. Zuteilung des Überschusses (falls vorhanden und Lademodus PV oder Zielladen) unter Berücksichtigung des Lastmanagements: Der verfügbare Strom wird unter allen Ladepunkten mit der gleichen Priorisierung aufgeteilt.

<img width="734" alt="kaskadiert Zähler" src="https://github.com/openWB/core/blob/wiki/docs/kaskadierte_zähler.png">

_Einstellungen -> Konfiguration -> Geräte und Komponenten_  
Zunächst muss ggf ein Gerät und für den EVU-Zähler und jeden Zwischenzähler eine Komponente angelegt werden. Wenn an einer Zuleitung nur Ladepunkte oder Verbraucher mit einer festen Leistung angeschlossen sind und kein physischer Zähler verbaut ist, kann auch ein virtueller Zähler als Zwischenzähler angelegt werden (Loadsharing).

_Einstellungen -> Konfiguration -> Lastmamangement_  
Bei der Konfigurationn in der Abbildung sorgt das Lastmanagement dafür, dass Ladepunkt 2 und 3 gemeinsam nicht die maximale Stromstärke des virtuellen Zählers überschreiten. Außerdem berechnet das Lastmanagement die Ladeströme so, dass der virtuelle Zähler, Ladepunkt 1 und der vom EVU-Zähler gemessene Hausverbauch die vorgegebene maximale Leistung und Stromstärke des EVU-Zählers einhalten.

### Virtuelle Zähler
Ein virtueller Zähler addiert alle Komponenten, die in der Hierachie unterhalb dessen angeordnet sind, und die Leistung, die in den Einstellungen unter _zusätzlicher Verbrauch_ angegeben ist. Wenn sich mehrere Ladepunkte eine Zuleitung teilen (Loadsharing), muss ein virtueller Zähler konfgiuriert werden und in der Hierachie über den beiden Ladepunkten angeordnet werden. In der Abbildung sind das Ladepunkt 2 und 3.