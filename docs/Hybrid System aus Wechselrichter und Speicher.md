Bei Hybrid-Systemen ist der Speicher an den Wechselrichter angeschlossen. Bei den meisten Herstellern wird dann die Speicherleistung mit der PV-Leistung des Wechselrichters verrechnet und die ins Hausnetz abgegebene Leistung ausgegeben. Auch die Zählerstände werden miteinander verrechnet. In openWB wird die PV-Leistung und Speicher-Leistung getrennt ausgegeben.

Wenn die PV-Leistung um die Ladeleistung des Speichers zu niedrig ist, liegt ein Hybrid-System vor. (Achtung: Auch der Hausverbrauch stimmt dann nicht, da dieser aus den gemessenen Größen berechnet wird.)

Das Verrechnen von Hybrid-Systemen erfolgt automatisch und muss nicht im Wechselrichter-Modul implementiert werden. Wenn ein Hybrid-System vorhanden ist und die Speicher-Leistung aus der Wechselrichter-Leistung herausgerechnet werden muss, ordne den Speicher in der Hierarchie unter dem Wechselrichter an.

Bei einem Hybrid-System wird der Speicher in der Hierarchie hinter dem Wechselrichter angeordnet:
<img width="734" alt="hybrid" src="https://github.com/openWB/core/blob/wiki/docs/hybrid.png">

Im Vergleich dazu die Standard-Konfiguration:
<img width="734" alt="standard" src="https://github.com/openWB/core/blob/wiki/docs/standard.png">
