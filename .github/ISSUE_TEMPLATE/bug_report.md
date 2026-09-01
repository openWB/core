---
name: Bug report
about: Fehlerbericht für einen Bug
title: "[BUG]"
labels: bug
assignees: ''

---

> Hier bitte ausschließlich Bugs melden und keine Fragen posten!

Bei Problemen zur **Inbetriebnahme / Anschluss, Bugs oder Hardwareproblemen** mit openWB-Hardware bitte direkt über die **Support-Funktion** unter `Einstellungen -> System -> Support` an openWB wenden (notfalls auch per Mail an support@openwb.de).

Bitte keine Mehrfach-Meldung per Mail, Support-Ticket und Forum.  
Das spart auf unserer Seite Supportzeit und bringt erfahrungsgemäß keine Beschleunigung des Vorgangs.

## Bitte bei Problemen immer einen ungekürzten Logauszug posten:

- Dazu unter `System -> Fehlersuche` das Debuglevel auf **Details** stellen und mindestens zwei komplette Durchläufe von `# ***Start***` bis `# ***Start***` aus dem Main-Log kopieren, **während das Problem auftritt**. Sensible Daten wie Benutzernamen und Kennwörter unkenntlich machen.  
  Alternativ das Log hier hochladen:  
  https://paste.openwb.de/  
  und den Link im Thread posten. Die Logs werden dort automatisch nach 90 Tagen gelöscht. Bitte keine gezippten Logfiles hochladen!

- Diesen Bereich kopieren und unter Verwendung von Code-Tags (Button mit `</>` über dem Editor-Fenster) in den passenden Forumsthread einstellen. Je mehr Informationen bekannt sind, desto einfacher kann geholfen werden.

- Bei Problemen mit dem internen Ladepunkt zusätzlich einen Auszug aus dem Log des internen Ladepunkts posten, bei Problemen mit dem SoC zusätzlich einen Auszug aus dem SoC-Log.

- Bei Problemen mit dem UI/Darstellung bitte ein openWB-Theme verwenden, z. B. `Standard/Classic` oder `Koala` (wird bei der Themeauswahl angezeigt).

---

## Screenshots und einzelne Logzeilen ersetzen keinen Logauszug!

Falls Screenshots benötigt werden, bitte entweder das openWB-Theme **Standard/Classic** oder **Koala** verwenden.

Für Beiträge wie:

> "Funktion XY geht nicht mehr! Woran kann das liegen?"

ohne Logs gibt es von uns keine Hilfestellung.

---

## Bitte zu jedem Problem mit angeben:

- Laufen Fremdsysteme parallel? (`HomeAssistant`, `IOBroker` o. ä. können Probleme verursachen)
- openWB Version?
- openWB Variante?  
  (`Selbst installiert`, `Standalone`, `series1/2`, `Standard(+)`, `Pro(+)`, `Buchse`, `Satellit`)
- Wenn selbst installiert: welches OS?
- Browser-Cache gelöscht? (bei Problemen mit dem UI)
- Welches Theme? (bei Problemen mit dem UI)

---

## Je nach Problem:

- Welches PV-Modul / welcher Wechselrichter?
- Welches EVU-Modul?
- Welches Speichermodul?
- Welches Auto wird geladen?
- Welche Hierarchie im Lastmanagement? (Screenshot Struktur)
- usw.

---

# Issues OHNE diese Angaben werden kommentarlos geschlossen.
