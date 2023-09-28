Dieser Beitrag erklärt, wie Einstellungen für ein Element aus einer Auswahlliste anhand einer Vorlage erstellt werden. Zu diesen Elementen zählen: Geräte, Komponenten, Fahrzeug(SoC)-Module und Backup-Clouds.

Die Installation des GUI-Repositories ist in eben diesem beschrieben: [openwb-ui-settings](https://github.com/openWB/openwb-ui-settings)

Die Auswahllisten werden dynamisch erzeugt. Damit euer Element darin enthalten ist, muss im entsprechenden Ordner im Core-Repo eine config.py-Datei wie in den Samples beschrieben enthalten sein. Wenn keine Einstellungsseiten in vue hinterlegt sind, sind die Einstellungen als json-Objekt editierbar. Dies ist für einen PR im Core-Repo ausreichend. Wie Ihr auch einen PR im GUI-Repo für die Einstellungen erstellen könnt, erklären wir Euch hier am Beispiel eines Fahrzeugs:

### Einstellungen erzeugen
Im Ordner src/components des GUI-Repos legt Ihr im Ordner `vehicles` einen neuen Ordner `sample` an. Dort hinein kopiert Ihr die Vorlage aus dem Ordner [samples_gui](https://github.com/openWB/core/tree/master/docs/samples/samples_gui) und ersetzt sample durch den Namen eures neuen Fahrzeugs. Bitte auf die Groß- und Kleinschreibung achten.

Nun müssen noch Frames für einzelnen Einstellungen ergänzt werden. Dafür könnt Ihr euch entweder an den bereits existierenden Modulen orientieren oder die Beispiele nutzen, die Ihr euch im GUI unter Einstellungen -> Beispiele anschauen könnt. Die Frames findet Ihr [hier](https://github.com/openWB/openwb-ui-settings/blob/main/src/views/TestingStore.vue).

`:model-value="$store.state.examples.text3"`  
`@update:model-value="updateState('text3', $event)"`  
Diese beiden Zeilen gibt es in jedem Frame. Die erste Zeile gibt den Wert an, der vom Broker gelesen werden soll. Die zweite den Wert, der aktualisiert werden soll. 
Für die Einstellungen müssen die Zeilen immer so aussehen:  
`:model-value="configuration.sample"`  
`@update:model-value="updateConfiguration($event, 'configuration.sample')`

Dann werden die Einstellungen automatisch dem richtigen Topic im Broker zugeordnet. Wichtig ist, dass sample immer genau so heißt, wie die Einstellung in der config.py. Nach dem Tag `<template #help>` könnt Ihr einen Hilfetext eingeben, der angezeigt wird, wenn man auf das Fragezeichen klickt.

### Pull Request stellen
Die kompilierten vue-Dateien im Core-Repo können nicht gemergt werden. Deshalb dürfen im PR des Core-Repos keine kompilierten vue-Dateien enthalten sein. Für die Einstellungs-Seiten bitte einen PR im openwb-ui-settings-Repo stellen. Nach dem Mergen kompilieren wir die vue-Dateien neu und aktualisieren diese im Core-Repo.

_Bei Fragen programmiert Ihr die Einstellungs-Seite vorerst, wie Ihr es versteht, und erstellt einen (Draft-)PR. Wir unterstützen Euch gerne per Review._