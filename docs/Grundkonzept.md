Hier werden die Grundeinstellungen für Anfänger mit einer einfachen Konstellation, welche im privaten Umfeld häufig vorkommt, erklärt.
Üblicherweise sind da ein oder zwei Autos und ein oder zwei Wallboxen, die bei der software2 nur noch openWBs sein dürfen. Hat man nur ein Auto und eine openWB, ist es ganz simpel. Mit zwei Autos muss man sich - wenn man weiterreichende Features nutzen - oder nur ganz einfach die geladenen kWh loggen möchte - damit auseinandersetzen, wie man der openWB mitteilt, welches Auto nun angeschlossen ist:

- man wählt das zu ladende Auto auf dem Handy oder auf dem Display der openWB aus
- man macht das bei mit RFID-Leser ausgestatteten openWBs per RFID-Karte
- man kauft für jedes Auto eine eigene openWB; das hat den Vorteil, dass die Autos immer eingesteckt bleiben können und so der gesamte PV-Überschuss garantiert in den Autos landet.
- man gibt ein bisschen mehr Geld aus, kauft eine openWB pro und hat auch die richtigen Autos dafür, dass die Wallbox selbst das Auto erkennt. Da geht das automatisch und das ist neu in der Software2; alternativ kann auch ein optionaler RFID-Leser an die Pro angeschlossen werden und zur Identifizierung des Fahrzeugs verwendet werden.

## Konfiguration

Die Konfiguration der Wallbox-Funktionalität verteilt sich auf zwei oder drei Menüpunkte im Konfigurations-Menü: Ladepunkte (ggf. Lastmanagement) und Fahrzeuge.

### Ladepunkte - die Infrastruktur

Hier werden die vorhandenen Wallboxen als Ladepunkt angelegt und ihnen gemeinsame Eigenschaften in Form von Ladepunkt-Profilen zugewiesen. Im privaten Bereich ist es ja üblicherweise so, dass mit maximal 11 kW geladen wird und die Ladepunkte entweder vor unbefugtem Zugriff geschützt werden wollen oder nicht. Das versteckt sich im Ladepunkt-Profil, weshalb wir uns um eigene Ladepunkt-Profile gar nicht kümmern müssen. Wir nehmen das Standard-Ladepunkt-Profil für alle unsere openWBs und passen das nach unseren Wünschen an.

Sind mehrere Ladepunkte an einer Unterverteilung angeschlossen, deren Zuleitung weniger verträgt, als die Ladepunkte abgeben können, muss man sich noch über das Loadsharing Gedanken machen. Zum Beispiel ist eine Unterverteilung, an der zwei 22 kW openWBs angeschlossen sind, in den seltensten Fällen mit den dafür notwendigen 63 A abgesichert; häufig z.B. nur 35 A. Hier fügt man noch eine Komponente "virtuellen Zähler" ein, setzt den im [Lastmanagement](https://github.com/openWB/core/wiki/Lastmanagement-und-kaskadierte-Zähler) in der Struktur über die beiden Ladepunkte und trägt dort die 24 kW / 35 A ein. Die maximal zulässige Leistung am EVU-Punkt trägt man dementsprechend in diesem [Zähler](https://github.com/openWB/core/wiki/Zaehler) ein.

### Fahrzeuge - warum wir das hier alles machen

Bei den Fahrzeugen zerteilt sich die Konfiguration in die technischen Eigenschaften und die ladungstechnischen Aspekte - das sind die beiden Profile für Fahrzeug und Ladung. Die beiden zusammengefasst ergeben das Fahrzeug.

#### Fahrzeug-Profile

Da steht drin, was für einen Fahrzeugtyp mit welchen Eigenschaften wir haben (ID.3, BMW i3, Tesla Model Y, ...) und Angaben zur Ladungssteuerung und -statistiken. Haben wir nur ein Auto oder interessiert Zielladen oder "geladene km" nicht, reicht es, beim Standard-Fahrzeug-Profil zu bleiben.

#### Ladeprofil

Da steht drin, wie das Auto geladen werden soll, aber diese Einstellungen sind später im UI der openWB alle änderbar. Bei mehr als einer openWB sollte man je Fahrzeug ein Ladeprofil anlegen, damit man z.B. von der neu hinzugekommenen Priorisierung Gebrauch machen kann. (Das priorisierte Auto fängt zuerst an zu laden, wenn man beide gleich priorisiert, muss der Überschuss wie bei der 1.9 für beide angeschlossenen Autos reichen.) Bei mehr als einem Auto sollte man auch je Auto ein Ladeprofil anlegen, denn da stehen die Zeitpläne und ein SoC-Limit drin. Einfacher ist es bei nur einem Auto - da reicht es wieder, beim Standard-Ladeprofil zu bleiben und das zu ändern. Allerdings wird das Standard-Ladeprofil (im Modus Stop) auch dafür genutzt, Ladepunkte nach Abstecken zu sperren. Möchte man also Ladepunkte vor unbefugtem Zugriff schützen, muss man auch bei einer Wallbox ein eigenes Ladeprofil anlegen.

#### Fahrzeug

Hier werden nun die beiden Profile zusammengeführt und ggf. ein SoC-Modul konfiguriert.

**Kurz zusammengefasst:** Mit einem Auto und einer openWB bleibt man bei den Profilen immer bei den mitgelieferten Standard-Profilen und ändert die Parameter dort. Bei mehreren Autos legt man für jedes Auto ein Fahrzeug-Profil und ein Ladeprofil an und fasst die beiden im Fahrzeug zusammen.

Danke für das Erstellen dieses Howto an [Gero](https://openwb.de/forum/viewtopic.php?t=8076)
