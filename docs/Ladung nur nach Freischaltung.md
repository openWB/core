Die openWB bietet die Möglichkeit den Ladepunkt gegen ungewollten Zugriff zu schützen.
Diese Option ist vor allem für öffentlich zugängliche Ladepunkte sinnvoll aber auch im privaten Bereich nützlich.
Dazu gibt es zwei grundlegende Konzepte:

#### **A** Nach Abstecken des Fahrzeugs wird der Ladepunkt gesperrt (Sperre nach Abstecken)

Ein neuer Ladevorgang erfolgt erst nach Freischalten durch:

- Eingeben einer **PIN** am openWB-Display (sofern mit Touchdisplay)
- Vorhalten eines **RFID-Tags** an der openWB mit RFID-Reader
- Fahrzeugerkennung über den **Ladestecker** mit der openWB-Pro
- händisches Entsperren des Ladepunktes im User Interface

#### **B** Nach Abstecken des Fahrzeugs wird auf das Standardfahrzeug (Standard nach Abstecken) mit Lademodus **Stop** gewechselt

Ein neuer Ladevorgang erfolgt erst durch:

- auswählen eines Fahrzeugs mit Lademodus Sofortladen, PV- oder Zielladen
- händischer Wechsel des Lademodus oder Fahrzeuges im User Interface
- vorhalten eines ID-Tags, welcher einem Fahrzeug zugeordnet ist

#### Allgemeine Konfiguration

Wenn ID-Tags genutzt werden sollen, dann ist in der Navigationsbar unter **Einstellungen - Optionale Hardware** unter dem Punkt Identifikation von Fahrzeugen die Option **Identifikation aktivieren** auf **An** zustellen.

**I.** Fahrzeuge
In der Navigationsbar auf Einstellungen klicken, dann den Reiter Konfiguration auswählen und **Fahrzeuge** aufrufen. Standardmäßig ist hier das **Standard-Fahrzeug** angelegt, welches die Option **Zugeordnete ID-Tags** beinhaltet. Hier müssen die ID-Tags eingetragen werden, welche ausschliesslich zur Zuordnung von Fahrzeugen verwendet werden. Hier zeigt sich auch die Stärke der openWB im Fahrzeugkonzept, welches die Möglichkeit bietet, verschiedene Fahrzeuge mit verschiedenen Fahrzeug- und Ladeprofilen über die ID-Kennung aufzurufen.

Hier muss für jedes Fahrzeug mit Freischaltwunsch ein **separates Fahrzeug** angelegt werden und die jeweiligen ID-Tags eingetragen werden, die zur Zuordnung genutzt werden.

Achtung: Lade-Profile müssen den Fahrzeugen unter Fahrzeuge zugeordnet werden!

**II.** Ladepunkte
In der Navigationsbar auf Einstellungen klicken, dann den Reiter Konfiguration auswählen und **Ladepunkte** aufrufen.
Standardmäßig ist hier das **Standard-Ladepunkt-Profil** angelegt, welches die Option **Sperre nach Abstecken** bietet. Wird diese Option aktiviert, dann ist das Feld **Zugeordnete ID-Tags** zugänglich.
Hier müssen die ID-Tags eingetragen werden, welche ausschliesslich zur Entsperrung des Ladepunktes verwendet werden. Sind mehrere Ladepunkte vorhanden (z.B. Duo oder mehrere ferngesteuerte openWBs) kann für jeden Ladepunkt ein eigenes Ladepunkt-Profil angelegt werden, wobei hier jeweils eine eigene ID-Kennung zur Freischaltung hinterlegbar ist.

Achtung: Ladepunkt-Profile müssen den Ladepunkten unter Ladepunkte zugeordnet werden!

##### Anmerkung: Bei allen Anpassungen der Einstellungen Speichern nicht vergessen!

Zu **A. Sperre nach Abstecken** ist folgendes zu konfigurieren:
Die Option **Sperre nach Abstecken** ist im **Ladepunkt-Profil** bei Ladepunkte auswählbar und bewirkt, dass der Ladepunkt nach Abstecken eines Fahrzeugs gesperrt wird. Es gibt hier dann folgende zwei Möglichkeiten diesen Ladepunkt wieder zu entsperren:

1. die Option *Ladepunkt sperren* händisch im User Interface auf Nein setzen. Dadurch startet nach Anstecken eines Fahrzeugs das voreingestellte Fahrzeug den Ladevorgang.
2. ein ID-Tag vorhalten, der im Ladepunkt-Profil hinterlegt ist. Dadurch wird der Ladepunkt automatisch entsperrt und das voreingestellte Fahrzeug startet den Ladevorgang. Ist der ID-Tag, welcher im Ladepunkt-Profil hinterlegt wurde identisch mit einem ID-Tag, der einem Fahrzeug zugeordnet ist, dann findet hier auch direkt eine Zuordnung zu einem Fahrzeug statt. Dabei wird der Ladepunkt entsperrt und das dem ID-Tag zugeordnete Fahrzeug startet den Ladevorgang.

Wurden mehrere Fahrzeuge mit demselben ID-Tag angelegt, dann startet das Fahrzeug den Ladevorgang, welches auf der Liste der Fahrzeuge dem ID-Tag zuerst zugeordnet wurde.
Solange der Ladepunkt gesperrt ist, wird kein gültiger ausschliesslich einem Fahrzeug zugeordneter ID-Tag akzeptiert.
Nach Starten eines Ladevorgangs wird kein neuer ID-Tag akzeptiert.

Anmerkung: Im Fall, dass zwei oder mehrere Fahrzeuge mit unterschiedlichen ID-Tags an demselben (gesperrten) Ladepunkt laden dürfen, müssen beide ID-Tags der Fahrzeuge auch im Ladepunkt-Profil hinterlegt werden. Dadurch wird erstens der Ladepunkt entsperrt und zweitens das dem Fahrzeug zugeordnete Lade-Profil ausgewählt, wodurch dann das damit verknüpfte Fahrzeug mit den dort hinterlegten Ladeeinstellungen den Ladevorgang startet.

Zu **B. Standard nach Abstecken** ist folgendes zu konfigurieren:
Die Option **Standard nach Abstecken** ist im **Lade-Profil** bei Fahrzeuge auswählbar. Diese Option macht nur Sinn, wenn neben dem Standard-Lade-Profil mindestens ein weiteres Lade-Profil und mindestens ein weiteres Fahrzeug angelegt wurde. Dabei ist dem Standard-Fahrzeug das Standard-Lade-Profil und dem weiteren Fahrzeug das weitere Lade-Profil zuzuweisen.
Um diese Option sinnvoll zu nutzen, muss im Standard-Lade-Profil unter Allgemeine Optionen der aktive Lademodus auf **Stop** gestellt werden.
Weiterhin muss in einem anderen zu nutzenden Lade-Profil unter Allgemeine Optionen **Standard nach Abstecken** aktiviert werden.

Insofern der Ladepunkt nicht gesperrt wurde, kann über einen ID-Tag der Ladevorgang für ein dem ID-Tag zugeordnetes Fahrzeug (entweder Standardfahrzeug oder ein anderes Fahrzeug mit einem Lade-Profil verschieden vom Standard-Lade-Profil) gestartet werden. Nach Abstecken wechselt die Auswahl dann auf Standardfahrzeug in den Lademodus **Stop** und der Ladepunkt startet keinen weiteren Ladevorgang bis die Auswahl entweder händisch über das User Interface oder automatisch per ID-Tag geändert wird.

Startet ein Fahrzeug über einen ID-Tag den Ladevorgang und ist in diesem Fahrzeug Standard nach Abstecken aktiviert, dann wird nach Abstecken auf das Standardfahrzeug gewechselt, unabhängig davon, welches Fahrzeug vorher ausgewählt war.
Startet ein Fahrzeug über einen ID-Tag den Ladevorgang und ist in diesem Fahrzeug Standard nach Abstecken nicht aktiviert, dann wird nach Abstecken auf das letzte vorher ausgewählte Fahrzeug gewechselt.

### Use Cases

#### Sperre nach Abstecken

Sperre nach Abstecken kann an einem Ladepunkt verwendet werden, welcher das Laden gegenüber fremden Zugriff sichert. Wird der ID-Tag nur zum Sperren/Entsperren des Ladepunktes verwendet, dann startet immer das ausgewählte Fahrzeug den Ladevorgang. Dies kann im privaten Bereich mit nur einem Fahrzeug sinnvoll sein, damit nur dieses Fahrzeug auch laden darf. Die Option ist aber auch für Ladeparks sinnvoll, bei denen die Ladepunkte nur für eine Gruppe von ID-Tags freischaltbar sind und dem ID-Tag zum Entsperren auch gleichzeitig zugeordnet sind.

#### Standard nach Abstecken

Standard nach Abstecken kann an einem Ladepunkt verwendet werden, welcher das Laden mehrere verschiedener Fahrzeuge ermöglichen soll. Werden mehrere Fahrzeuge mit verschiedenen Lade-Profilen und verschiedenen ID-Kennungen neben dem Standard-Fahrzeug angelegt, kann über die ID-Kennung zwischen den einzelnen Fahrzeugen gewechselt werden. Hier bietet sich beispielsweise ein privater Ladepunkt mit zwei Fahrzeugen an oder ein Ladepunkt in einer Firma mit verschiedenen Mitarbeitern.

Standard nach Abstecken kann auch dazu verwendet werden, um beispielsweise zwischen zwei Fahrzeugen (und damit Fahrzeug-Profilen und Lade-Profilen) ohne ID-Tag zu wechseln, vor allem wenn nur eines der Fahrzeuge über die ID-Kennung zuverlässig erkannt wird.

Stand 02. Juli 2024
