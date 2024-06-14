Zunächts müssen auf dem Smartlogger300a folgdene Einstellungen festgelegt wernden

1. Zunächst unter Einstell.-> Bef.-Param. -> Modbus TCP
   Folgende Einstellungen festlegen:
     Leitungseinstellungen: Akt.(Unbegrenzt)
     Addressmodus: Logische Addresse
     Logger-Addresse: z.B.4 (Muss eine freie ModBus ID sein, logische Addresse 2tes Bild.)
     Schnelle Planung: Aktivieren
    ![Huawei Smartlogger ModBusTCP](HuaweiSmartloggerModBusTCP.PNG)
2.  Unter Wartung->Geräte-Mgmt.-> Geräte Liste
    Kann man jetzt die logische Adr. der einzelnen Geräte ablesen. Diese wird dann untern den Einstellungen in der openWB gebraucht (ModbusID)
    ![HuaweiSmartloggerLogischeAdressen](HuaweiSmartloggerLogischeAdressen.PNG)
4. in den Einstellungen der openWB das Modul Huawei Smartlogger auswählen.
5. Jetzt muss man die IP des Smartloggers und den Port 502 eintragen, außer dieser wurde geändert.
6. Hetezt die passenden Komponenten hinzufügen und die jeweilige ModbusID eintragen.
7. Zum schluss auf Speichern drücken und unter dem Lastmanagement die Passenden Andordnung wählen.
  ![Huawei Smartlogger Komponenten](HuaweiSmartloggerKomponenten.PNG)
