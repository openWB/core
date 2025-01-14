Der Hausverbrauch kann in der openWB auf zwei verschiedenen Wegen ermittelt werden: die openWB berechnet den Hausverbrauch oder du gibst in den Einstellungen einen Zähler an, der den Hausverbrauch misst.  
Eine Mischung der beiden Möglichkeiten, also nicht gemessener, berechneter Hausverbrauch und gemessener Hausverbrauch kann in der openWB nicht abgebildet werden.  
Es muss in der Anlage einen Zähler geben, der alle Verbräuche erfasst. Dies kann entweder der EVU-Zähler sein (dieser erfasst auch Wechselrichter und Speicher) oder der Hausverbrauchszähler (Wechselrichter und Zähler werden separat erfasst).

### Möglichkeit 1: Berechnung des Hausverbrauchs durch die openWB

Der Hausverbrauch entspricht der Summer aller nicht gemessenen Verbraucher. Üblicherweise ist am EVU-Punkt ein Zähler installiert. Außerdem kennt die openWB die Leistungen des Wechselrichters, des Speichers und der Ladepunkte. Aus der Differenz ergibt sich der Hausverbrauch.

### Möglichkeit 2: Hausverbrauchszähler

Unter `Einstellungen→Konfiguration→Lastmanagement` kann bei Hausverbrauch ein Zähler ausgewählt werden. Diese Einstellung ist nur dann richtig, wenn in der Anlage ein Zähler verbaut ist, der den Hausverbrauch misst. Dies ist bei manchen Systemherstellern wie Kostal(?) üblich. Der Hausverbrauchszähler kann die Ladepunkte messen oder nicht. Dann müssen diese in der Hierachie entsprechend hinter oder neben dem Zähler angeordnet werden.  
Bezug und Einspeisung ins öffentliche Netz werden dann mit einem virtuellen Zähler aus den Werten des Hausverauchszählers, Wechselrichter und Speicher berechnet. Der virtuelle Zähler addiert die Werte aller in der Struktur dahinter angeordneten Komponenten.

Zunächst ein Virtuelles Gerät mit einem virtuellen Zähler anlegen. Die Komponenten müssen in der Hierarchie wie in den Abbildungen unten angeordnet werden. In den Einstellungen für das Lastmanagement beim Punkt Hausverbrauch den Hausverbrauchs-Zähler auswählen.

### Hausverbrauch bei mehreren Zählern
Wenn es einen Zähler am EVU-Punkt und einen Zähler im Hausverbrauchszweig gibt, dann wie unter `Möglichkeit 2` beschrieben, den Zähler, der den Hausverbrauch misst unter `Einstellungen→Konfiguration→Lastmanagement→Hausverbauch` auswählen.  
Wenn der Hausverbrauch die Summer mehrerer Zähler in der Anlage ist, müssen diese in einem virtuellen Zähler zusammengefasst werden und dieser wie unter `Möglichkeit 2` als Hausverbrauchs-Zähler ausgewählt werden. Dieser kann nicht der Zähler an der Spitze (EVU-Zähler) sein, da in diesem Zähler immer auch Speicher und PV miteingerechnet werden müssen, um den Überschuss für PV-Laden am EVU-Punkt zu kennen.  

Misst der Zähler den Hausverbrauch, ergibt sich folgende Anordnung:

![Hausverbrauchs-Zähler](Hausverbrauchs-Zaehler.png)

Misst der Zähler den Hausverbrauchs und ist ein Hybrid-Wechselrichter vorhanden, ergibt sich folgende Struktur:

![Hausverbrauchs-Zähler Hybrid](Hausverbrauchs-Zaehler_Hybrid.png)

Ist der Zähler wie üblich am EVU-Punkt installiert und misst den gesamten Verbrauch/Einspeisung, muss die Struktur wie folgt aussehen:

![Standard Zähler](standard.png)
