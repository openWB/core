Nach Abstecken des Fahrzeugs soll der Ladepunkt gesperrt werden und eine neue Ladung erst nach Freischalten durch:

- Eingeben einer PIN am openWB-Display (sofern mit Touchdisplay) oder
- Vorhalten eines RFID-Tags an der openWB mit RFID-Reader oder
- Direkt-tagging über den Ladestecker mit der openWB-Pro oder
- Auswahl eines Fahrzeugs im User Interface

gestartet werden.

Hierzu ist folgendes zu konfigurieren:

1. für jedes Fahrzeug mit Freischaltwunsch unter Einstellungen -> Konfiguration -> Fahrzeuge zusätzlich zum Standard-Fahrzeug **ein separates Fahrzeug** anlegen
2. unter Lade-Profile -> **Standard-Lade-Profil** (wird nur dem Standard-Fahrzeug zugeordnet) -> **Lademodus auf Stop** stellen
3. ein **neues Lade-Profil** für Fahrzeuge mit Freischaltwunsch anlegen (z.B. RFID-Lade-Profil) und dort -> **Standard nach Abstecken** aktivieren sowie bevorzugten Lademodus wählen
4. den Fahrzeugen mit Freischaltwunsch **das Lade-Profil** für Fahrzeuge mit Freischaltwunsch **zuweisen** (z.B. RFID-Lade-Profil)
5. **Speichern** nicht vergessen

Wenn die Freischaltung mittels PIN, RFID oder MAC-Adresse erfolgen soll:

- Einstellungen -> Optionale Hardware: **RFID aktivieren** + Speichern
- unter Konfiguration -> Fahrzeuge -> gewünschtes Fahrzeug -> Zugeordnete Tags: dem jeweiligen Fahrzeug **den Tag (PIN/RFID-Tag/MAC-Adresse) zuweisen** + Speichern
- unter Konfiguration -> Ladepunkte -> Ladepunkt-Profile -> im gewünschten Ladepunkt-Profil: **Freischaltung mit RFID aktivieren und die gültigen Tags eintragen** + Speichern
