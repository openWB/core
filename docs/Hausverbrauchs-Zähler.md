Es gibt zwei mögliche Einbaupositionen für Zähler: EVU-Punkt und Hausverbrauchs-Zweig.
Ist der Zähler am EVU-Punkt installiert, misst er am EVU-Punkt (EVU=Elektrizitätsversorgungsunternehmen) Bezug und Einspeisung ins öffentliche Netz. Der Hausverbrauch wird dann aus den Werten der Ladepunkte, Wechselrichter und Speicher berechnet.
Ist der Zähler im Hausverbrauchs-Zweig installiert, misst er die Leistung der Ladepunkte und den Hausverbrauch. Bezug und Einspeisung ins öffentliche Netz werden dann aus den Werten des Zählers, Wechselrichter und Speicher berechnet. Dazu gibt es in openWB einen virtuellen Zähler. Dieser addiert die Werte aller in der Struktur dahinter angeordneten Komponenten.

Zunächst ein Virtuelles Gerät mit einem virtuellen Zähler anlegen. Die Komponenten müssen in der Hierarchie wie in den Abbildungen unten angeordnet werden. In den Einstellungen für das Lastmanagement beim Punkt `Hausverbrauch` den Hausverbrauchs-Zähler auswählen. Der Hausverbrauch ist die Leistung des ausgewählten Zählers abzüglich der Ladeleistung.

Misst der Zähler den Hausverbrauch, ergibt sich folgende Anordnung:

![Hausverbrauchs-Zähler](Hausverbrauchs-Zaehler.png)

Misst der Zähler den Hausverbrauchs und ist ein Hybrid-Wechselrichter vorhanden, ergibt sich folgende Struktur:

![Hausverbrauchs-Zähler Hybrid](Hausverbrauchs-Zaehler_Hybrid.png)

Ist der Zähler wie üblich am EVU-Punkt installiert und misst den gesamten Verbrauch/Einspeisung, muss die Struktur wie folgt aussehen:

![Standard Zähler](standard.png)
