Zunächst einen neuen Ordner erstellen/auswählen, in den die Sicherungen hochgeladen werden sollen.

Nachfolgende Schritte müssen auf dem Bereitstellenden system geamcht werden
1. SMB Freigabe erstellen (Auf NAS etc.)
2. User einrichten und berechtigen - R/W

Nachfolgende Schritte müssen in openwb gemachte werden.
1. IP Adresse oder Name (Am besten FQDN) im Feld Server hinterlegen
    * IP: z.B 192.168.178.1
    * Name z.B. mein-server
    * FQDN z.B mein-server.fritz.box
2. Share angeben in dem das Backup gespeicher werden soll
3. Optional können ein bis n Unterordner angegeben werden. Diese müssen immer mit / getrennt werden und auch am Ende muss ein / stehen
    * Beispiel: test/ oder aber test1/test2/test/
4. Benutzer und Passwort in die jeweilegen Felder eintragen

![Samba nutzen](Samba.png)
