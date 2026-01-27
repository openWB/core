# Benutzerverwaltung

Kevin hat vorgeschlagen, die offenen Punkte in zwei Schritten in den Master zu bringen. Die erste Gruppe umfasst die Punkte 1. bis 3., im zweiten Schritt kommen dann 4. und 5.

## Offene Punkte

### 1. Display mit aktivierter Benutzeranmeldung

Dem Browser sind in geeigneter Weise Anmeldedaten zu übergeben. Dafür wird ein neuer Benutzer angelegt (automatisch mit festem Namen?) und die Anmeldedaten lokal abgelegt.

Der Kiosk-Modus für das lokale Display startet ein Inkognito-Fenster! In diesem Modus werden keine Cookies oder sonstige Daten gespeichert. Das ist notwendig, um z.B. die Willkommen-Seite und den Cache zu deaktivieren.

Es gibt keine Möglichkeit, einen Cookie einer Konfigurationsdatei zu hinterlegen. Chromium verwendet SQLite zum Speichern und verschlüsselt die Cookies aus Sicherheitsgründen. Daran würde auch der Betrieb im normalen Fenster nichts ändern. Bleibt also lediglich die Möglichkeit, die Anmeldedaten an die URL anzuhängen. Entweder als URL-Parameter oder als Anmeldedaten für eine Authentifizierung.

### 4. Anbindung von secondaries

Die Kommunikation wird immer von der primary aufgebaut. Entweder werden Sollwerte in den Broker der secondary geschrieben oder aktuelle Messdaten abgerufen. Das bedeutet, dass bei aktivierter Benutzerverwaltung auf einer secondary, dort ein Benutzer für die primary angelegt werden muss. Mit diesem Benutzer baut dann die primary die Kommunikation auf.

Es wäre denkbar, dass eine secondary beim Hinzufügen zu einer primary mehr oder weniger automatisch konfiguriert wird. Wichtige Punkte hierfür:

Abgleich der Einstellungen:

1. "unverschlüsselter Zugang"
2. "Benutzerverwaltung aktiv"

Falls die Benutzerverwaltung aktiviert ist:

1. Kennwort des Administrators übertragen?
2. Benutzer für die primary anlegen und Kennwort setzen
3. Zugangsdaten für das Display an die secondary übergeben (siehe "1. Display mit aktiver Benutzeranmeldung")

## In Bearbeitung

## Erledigte Punkte

### 2. "Passwort vergessen" Funktionalität

Im Anmeldedialog wird eine Option "Passwort vergessen" ergänzt. Es erscheint dann ein neues Feld, in welchem eine E-Mail Adresse einzugeben ist. Diese Adresse wird dann an das Backend geschickt.

Das Backend muss nun prüfen, ob diese E-Mail auch einem Benutzer zugeordnet ist. Die E-Mail ist in dem Feld "textname" hinterlegt. Leider wird über `mosquitto_ctrl` dieser Wert nicht mit ausgegeben. Entweder, die Daten werden per MQTT über `$CONTROL/dynamic-srcurity/v1` angefordert, oder es wird direkt auf die Datei `var/lib/mosquitto/dynamic-security.json` zugegriffen, um den passenden Benutzer zu finden.

Ist die E-Mail gültig, dann wird eine zufällige Zeichenfolge als "Token" erzeugt, lokal mit Benutzername und Zeitstempel abgespeichert und über unseren "Forgot Password" Dienst als Mail verschickt.

Bei der Anmeldemaske gibt es jetzt die Option "mit Token anmelden". In diesem Dialog ist der Benutzername, das erhaltene Token sowie ein neues Passwort (inkl. Wiederholung) einzugeben. Diese Daten werden dann an das Backend geschickt.

Das Backend prüft, ob Benutzername und Token zu den lokal gespeicherten Daten passen und ob das Token eine gewisse Gültigkeitsdauer nicht überschritten hat (30 Minuten?). Ist die Prüfung erfolgreich, dann kann mit `mosquitto_ctrl dynsec setClientPassword <username> <newPassword>` das neue Kennwort für den Benutzer gespeichert werden.

### 3. Versionierung der hinterlegten Rollen inkl. ACLs

In der Datei `/var/lib/mosquitto/dynamic-security.json` speichert der Mosquitto die aktuellen Zugriffsrechte. Dort sind leider keine Kommentare enthalten, sodass die aktuell in mehreren Dateien genutzte Versionskennung "openwb-version:XXX" nicht umgesetzt werden kann.

Ebenfalls beinhaltet die Datei sowohl die Einstellungen aus `default-dynamic-security.json` als auch die dynamisch ergänzten Rollen aus `role-templates.json`. Das hat zur Folge, dass die Datei nicht einfach überschrieben werden kann, sondern der Inhalt strukturiert angepasst werden muss.

Als ersten Ansatz habe ich eine Rolle ohne ACLs mit dem Namen "openwb-version:1" erstellt. Die Version musste im Namen untergebracht werden, da über das Hilfsprogramm `mosquitto_ctrl` zu Rollen nur der Name und die gesetzten ACLs ausgelesen werden können. So kann die aktuelle Version mittels `mosquitto_ctrl listRoles | grep "openwb-version:"` ermittelt werden. Da die Rolle auch in `default-dynamic-security.json` enthalten ist, kann ein notwendiges Upgrade erkannt werden.

Das eigentliche Upgrade der Rollen ist noch auszuarbeiten.

### 5. Wechsel von Branches mit aktiver Benutzerverwaltung ohne Lockdown der openWB

Für die Benutzerverwaltung wurden die Konfigurationsdateien des öffentlichen Mosquitto Brokers überarbeitet.

Bis jetzt gab es im Ordner `/etc/mosquitto/conf.d` nur die Datei `openwb.conf`. Im Zuge der Benutzerverwaltung war eine Aufteilung dieser Datei sinnvoll, sodass es jetzt Dateien gibt, die in einem älteren Branch nicht beachtet werden. Da sich die Inhalte teilweise überschneiden, kommt es zu Fehlern beim Start des externen Brokers und die openWB ist für den Benutzer "gestorben".

Das Problem wurde bereits beim "zurücksetzen auf Werkseinstellungen" sowie der Wiederherstellung aus einer Sicherung behoben, indem alle vorhandenen Konfigurationsdateien entfernt und beim Start des openwb2 Dienstes neu angelegt werden. Analog sollte dies auch beim Wechsel eines Branches passieren, was jedoch eine entsprechende Logik in dem jeweiligen Branch voraussetzt. Alternativ müssten bereits vor dem Wechsel (Branch oder Tag) die Konfigurationsdateien entfernt werden.
