### PV-Laden
Beim PV-Laden wird die Ladeleistung anhand des Überschusses am EVU-Punkt geregelt. Um ständiges Starten und Stoppen der Ladung zu verhindern, startet die Ladung, wenn für die Dauer der Einschaltverzögerung die Einschaltschwelle überschritten wurde. Die Ladung wird gestoppt, wenn für die Dauer der Abschaltverzögerung die Abschaltschwelle unterschritten wurde.  
Wenn ein Wechselrichter verbaut ist, bei dem die Einspeiseleistung reduziert wird - auch als 70%-Regelung bekannt -, kann dies mit dem Regelpunkt Einspeisegrenze eingestellt werden.

### Regelmodus

Die Ladeleistung kann nicht mit absoluter Genauigkeit eingestellt werden, sodass am EVU-Punkt nicht auf exakt 0W geregelt werden kann. Einige Fahrzeuge und ältere openWBs können zudem nur in Schritten von 1A regeln (entspricht 230W bei einphasiger Ladung). Der Regelmodus bestimmt, in welchem Bereich (ca. 200-300W) sich der EVU-Überschuss bewegen soll. Beim Regelmodus „Bezug“ darf ein geringer Netzbezug vorhanden sein, bevor nachgeregelt wird. Das Auto lädt dann etwas schneller, aber es wird mehr Netzstrom verbraucht. Im Regelmodus „Einspeisung“ kann etwas Strom ins Netz eingespeist werden, bevor nachgeregelt wird. Dann lädt das Auto etwas langsamer und es wird weniger Netzstrom verbraucht.  
Der Regelbereich wird auf den gesamten Überschuss angewendet, bevor die PV-Regelung durchgeführt wird. D.h. der Regelbereich wird auf alle Einstellungen für das PV-Laden angewendet und nur einmal unabhängig von der Anzahl der angesteckten Fahrzeuge. Liegt der Überschuss am EVU-Punkt im vorgegebenen Regelbereich, wird nicht nachgeregelt. Liegt er außerhalb des Bereichs, wird die Lade-Leistung auf die Mitte des Bereichs angepasst.  
Bei Speichervorrang erzeugt die Regelung bei Bedarf unabhängig vom eingestellten Regelmodus Einspeisung, damit der Speicher seine Ladeleistung erhöht.

Achtung: bei unlogischen Einstellungen kann die Regelung gestört werden! Im Zweifel bitte unsere vordefinierten Modi verwenden.

#### Speicherbeachtung

Sofern ein Hausstromspeicher (im Folgenden „Speicher“ genannt) im Energiesystem verbaut ist, kann dieser beim Fahrzeugladen mit berücksichtigt werden. Dies erfolgt passiv über die Berücksichtigung der Speicherleistungswerte und des Speicher-SoC. Eine aktive Speichersteuerung durch openWB ist aktuell mangels Speicherschnittstelle nicht möglich.  
Bei Auswahl „Fahrzeuge“ wird der gesamte Überschuss in das EV geladen. Ist die maximale Ladeleistung der Fahrzeuge erreicht und es wird eingespeist, wird dieser Überschuss in den Speicher geladen.  
Bei Auswahl „Speicher“ wird der gesamte Überschuss in den Speicher geladen. Ist die maximale Ladeleistung des Speichers erreicht und es wird eingespeist, wird dieser Überschuss unter Beachtung der Einschaltschwelle in die Fahrzeuge geladen.  
Bei Auswahl „Mindest-SoC des Speichers“ wird der Überschuss bis zum Mindest-SoC in den Speicher geladen. Ist die maximale Ladeleistung des Speichers erreicht und es wird eingespeist, wird dieser Überschuss in die Fahrzeuge geladen. Wird der Mindest-SoC überschritten, wird der Überschuss ins Fahrzeug geladen.