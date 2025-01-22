Mit den verschiedenen Identifikations-Möglichkeiten kannst du die openWB grundsätzlich vor unbefugtem Laden schützen oder fahrzeugbasierte Funktionen nutzen. Es gibt zwei grundlegende Konzepte: Das Entsperren eines Ladepunkts und das Zuordnen eines Fahrzeugs.

Die Identifikation erfolgt über

  * RFID-Tags: Setzt einen eingebauten RFID-Reader voraus. Dieser ist als optionales Zubehör für openWB Pro und openWB series2 erhältlich. Der Tag kann nach oder max. 5 Minuten vor dem Anstecken gescannt werden.
  * Eingabe einer ID am Display: Setzt ein eingebautes Display voraus.
  * Fahrzeugerkennung: Setzt eine openWB Pro und ein Fahrzeug, das diese Funktion unterstützt, voraus. (Permalink zur Übersicht im Forum) Zur Identifikation wird die MAC-Adresse des Fahrzeugs verwendet. Hat die Pro auch einen RFID-Reader, hat bei der Fahrzeug-Zuordnung die MAC-Adresse die höhere Priorität. Beim Entsperren wird beides geprüft.  

Die beschriebenen Identifikationsverfahren werden in der Software gleich ausgewertet. Es sind unterschiedliche Wege je nach Hardwareausstattung, die Information an die Software zu übergeben. Wenn ID-Tags genutzt werden sollen, dann ist in der Navigationsbar unter Einstellungen - Optionale Hardware unter dem Punkt Identifikation von Fahrzeugen die Option Identifikation aktivieren auf An zu stellen.

Zusätzlich kann das Entsperren und die Fahrzeug-Auswahl auch manuell im Web-GUI oder am Display durchgeführt werden.

#### Ladepunkt entsperren

Unter Einstellungen → Konfiguration → Ladepunkte → Ladepunkt-Profil kann für eine Gruppe von Ladepunkten die gültigen ID-Tags hinterlegt werden. Ist der Ladepunkt gesperrt und es wird einer der hinterlegten Tags gescannt/eingegeben, wird der Ladepunkt entsperrt. Mit der Option Sperren nach Abstecken wird nach dem Abstecken der Ladepunkt gesperrt und muss bei nächsten Abstecken erst entsperrt werden, bevor geladen werden kann.

#### Fahrzeug zuordnen

Im Menü Einstellungen → Konfiguration → Fahrzeuge können ID-Tags für das Fahrzeug hinterlegt werden. Wird einer dieser Tags erkannt, wird das Fahrzeug dem Ladepunkt zugeordnet.

Im Ladeprofil kann eingestellt werden, ob nach dem Abstecken das Standard-Fahrzeug zugeordnet werden soll. Andernfalls wird nach Abstecken das letzte vorher ausgewählte Fahrzeug zugeordnet.  
Die Option Standard nach Abstecken macht nur Sinn, wenn neben dem Standard-Fahrzeug mindestens ein weiteres Fahrzeug und neben dem Standard-Lade-Profil mindestens ein weiteres Lade-Profil angelegt wurde. Dabei ist dem Standard-Fahrzeug das Standard-Lade-Profil und dem weiteren Fahrzeug das weitere Lade-Profil zuzuweisen. Wenn nur mit Identifikation geladen werden soll, muss im Standard-Lade-Profil der aktive Lademodus auf Stop gestellt werden. In den Lade-Profilen der anderen Fahrzeuge muss Standard nach Abstecken aktiviert werden.  
Über den ID-Tag wird ein Fahrzeug zugeordnet. Nach Abstecken wechselt die Auswahl dann auf Standardfahrzeug in den Lademodus Stop und der Ladepunkt startet keinen weiteren Ladevorgang, bis die Auswahl entweder händisch über das User Interface oder automatisch per ID-Tag auf ein Fahrzeug geändert wird, das sich z.B. im Lademodus Sofortladen befindet und laden darf.

### Use Cases

#### Sperre nach Abstecken
 
Sperre nach Abstecken kann an einem Ladepunkt verwendet werden, welcher das Laden gegenüber fremdem Zugriff sichert. Wird der ID-Tag nur zum Sperren/Entsperren des Ladepunktes verwendet, dann startet immer das ausgewählte Fahrzeug den Ladevorgang. Dies kann im privaten Bereich mit nur einem Fahrzeug sinnvoll sein, damit nur dieses Fahrzeug auch laden darf. Die Option ist aber auch für Ladeparks sinnvoll, bei denen die Ladepunkte nur für eine Gruppe von ID-Tags freischaltbar sind und dem ID-Tag zum Entsperren auch gleichzeitig zugeordnet sind.

#### Standard nach Abstecken
Standard nach Abstecken kann an einem Ladepunkt verwendet werden, welcher das Laden mehrerer verschiedener Fahrzeuge ermöglichen soll. Werden mehrere Fahrzeuge mit verschiedenen Lade-Profilen und verschiedenen ID-Kennungen neben dem Standard-Fahrzeug angelegt, kann über die ID-Kennung zwischen den einzelnen Fahrzeugen gewechselt werden. Hier bietet sich beispielsweise ein privater Ladepunkt mit zwei Fahrzeugen an oder ein Ladepunkt in einer Firma mit verschiedenen Mitarbeitern. Standard nach Abstecken kann auch dazu verwendet werden, um beispielsweise zwischen zwei Fahrzeugen (und damit Fahrzeug-Profilen und Lade-Profilen) ohne ID-Tag zu wechseln, vor allem wenn nur eines der Fahrzeuge über die ID-Kennung zuverlässig erkannt wird.
