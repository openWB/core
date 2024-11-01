Das Gesetz sieht verschiedene Möglichkeiten für steuerbare Verbrauchseinrichtungen vor. Für jede steuerbare Verbrauchseinrichtung kann eine andere Option angemeldet werden. Bei der Konfiguration muss deshalb auch immer der/die Ladepunkte angegeben werden, für die die IO-Aktion angewendet werden soll.

### Dimmen
Beim Dimmen wird eine Mindestleistung für alle steuerbaren Verbrauchseinrichtungen nach einer vorgegebene Formel ermittelt. Das Ergebnis dieser Formel muss bei der IO-Aktion `Dimmen` in der Einstellung `Mindestleistung` eingetragen werden. ACHTUNG: Die openWB kann aktuell nur die Ladepunkte berücksichtigen. Sind noch weitere steuerbare Verbraucher angemeldet, muss dies bei der Ermittlung der Mindestleistung berücksichtigt werden. Die korrekte Ermitllung der Mindestleistung obliegt nicht der openWB.
Vorhandener Überschuss kann zusätzlich zur Mindestleistung verwendet werden.

### Dimmung per Direkt-Steuerung
Bei der Dimmung per Direkt-Steuerung wird jede steuerbare Verbrauchseinrichtung separat angesteuert und ihr Leistungsbezug auf 4,2 Kilowatt gedimmt.
Pro steuerbarer Verbrauchseinrichtung muss eine IO-Aktion konfiguriert werden und dort der Ladepunkt und der zugehörige Eingang angegeben werden.

### Rundsteuer-Empfänger-Kontakt (RSE)
Für den RSE-Kontakt kann ein Muster aus verschiedenen Eingängen und ein Prozentwert, auf den die Anschlussleistung begrenzt wird, angegeben werden.