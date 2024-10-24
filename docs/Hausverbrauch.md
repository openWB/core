Der Hausverbrauch kann in der openWB auf zwei verschiedenen Wegen ermittelt werden: die openWB berechnet den Hausverbrauch oder du gibst in den Einstellungen einen physischen Zähler an, der den Hausverbrauch misst.

### Berechnung des Hausverbrauchs durch die openWB

Der Hausverbrauch entspricht der Summer aller nicht erfassten Verbraucher. Üblicherweise ist am EVU-Punkt ein Zähler installiert. Außerdem kennt die openWB die Leistungen des Wechselrichters, des Speichers und der Ladepunkte. Aus der Differenz ergibt sich der Hausverbrauch.

### Hausverbrauchszähler

Unter `Einstellungen→Konfiguration→Lastmanagement` kann bei Hausverbrauch ein Zähler ausgewählt werden. Diese Einstellung ist nur dann richtig, wenn in der Anlage ein Zähler verbaut ist, der den Hausverbrauch misst. Dies ist bei manchen Systemherstellern wie Kostal(?) üblich. Der Hausverbrauchszähler kann die Ladepunkte messen oder nicht. Dann müssen diese in der Hierachie entsprechend hinter oder neben dem Zähler angeordnet werden.
Bezug und Einspeisung ins öffentliche Netz werden dann aus den Werten des Zählers, Wechselrichter und Speicher berechnet. Dazu gibt es in openWB einen virtuellen Zähler. Dieser addiert die Werte aller in der Struktur dahinter angeordneten Komponenten.

Zunächst ein Virtuelles Gerät mit einem virtuellen Zähler anlegen. Die Komponenten müssen in der Hierarchie wie in den Abbildungen unten angeordnet werden. In den Einstellungen für das Lastmanagement beim Punkt Hausverbrauch den Hausverbrauchs-Zähler auswählen.

Wenn der Hausverbrauch die Summer mehrerer Zähler in der Anlage ist, müssen diese in einem virtuellen Zähler zusammengefasst werden und dieser als Hausverbrauchs-Zähler ausgewählt werden. Dieser darf nicht der Zähler an der Spitze (EVU-Zähler) sein. Eine Mischung aus nicht erfasstem, berechnetem Hausverbrauch und gezähltem Hausverbrauch, kann in der openWB nicht abgebildet werden.

Misst der Zähler den Hausverbrauch, ergibt sich folgende Anordnung:

![Hausverbrauchs-Zähler](Hausverbrauchs-Zaehler.png)

Misst der Zähler den Hausverbrauchs und ist ein Hybrid-Wechselrichter vorhanden, ergibt sich folgende Struktur:

![Hausverbrauchs-Zähler Hybrid](Hausverbrauchs-Zaehler_Hybrid.png)

Ist der Zähler wie üblich am EVU-Punkt installiert und misst den gesamten Verbrauch/Einspeisung, muss die Struktur wie folgt aussehen:

![Standard Zähler](standard.png)
