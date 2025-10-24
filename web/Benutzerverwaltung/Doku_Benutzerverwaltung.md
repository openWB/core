# Benutzerverwaltung

## 1. Einleitung

Die software2 soll um eine Benutzerverwaltung erweitert werden. Dabei sollen die jeweiligen Rechte möglichst feingliedrig vergeben werden können.

Der einfachste Anwendungsfall ist der, dass die komplette Bedienung und Konfiguration nur nach erfolgreicher Anmeldung möglich ist. Nächste Variante ist, dass eine Bedienung zwar möglich, die Einstellungen jedoch ohne Anmeldung nicht zugänglich sind. Komplexere Fälle treten bei WEGs auf, wo der einzelne Zugriff auf Ladepunkte, Fahrzeuge und weitere Geräte/Komponenten zu regeln ist.

Die genauen Anforderungen und abzudeckende Einsatzfälle sind noch festzulegen. Abhängig von diesen Festlegungen ist schließlich die genaue technische Umsetzung zu planen, daher werden hier lediglich sinnvolle Leitlinien kurz vorgestellt.

Zusätzlich zu der reinen Benutzerverwaltung gibt es noch die Anforderung, dass die jetzigen Einstellungen optisch an das Koala Theme angepasst werden. Dabei sollen Synergieeffekte genutzt werden, sodass ein "Baukastensystem" aus kleinen Elementen ("Components") entsteht, welche sowohl in den Einstellungen als auch dem Koala Theme verwendet werden. So kann auch langfristig ein einheitliches Erscheinungsbild garantiert werden, ohne dass Elemente mehrfach gepflegt werden müssen.

## 2. Aktueller Stand der software2 im Hinblick auf die Benutzeroberflächen

### 2.1 Konfiguration des Webservers

Die Konfiguration des Apache2 Webservers ist so eingestellt, dass das Wurzelverzeichnis (zu erreichen über `http(s)://\<IP\>/`) auf `/var/www/html/` zeigt und somit eine Ebene über dem openWB-Verzeichnis und außerhalb des core Repository liegt. Es wird ein Zugriff über `http` und `https` erlaubt. Der verschlüsselte Zugriff wird mit einem selbst signierten Zertifikat abgesichert. Eine automatische Weiterleitung von `http` nach `https` gibt es nicht.

Für die verschiedenen Benutzeroberflächen wird die Verbindung zum MQTT-Broker ebenfalls vom Webserver bereitgestellt. Der Vorteil im Vergleich mit dem separaten Port der Version 1.9.x ist, dass weniger bis keine Probleme mit eventuell blockierten Ports auftreten. Der Zugriffspunkt für die Websocket-Verbindung ist `http(s)://\<IP\>/ws`. Zusätzlich wird derzeit noch aus Kompatibilitätsgründen `http(s)://\<IP\>/mqtt` eingerichtet. Die Verbindung zwischen Webserver und Broker ist unverschlüsselt, da alles unter "localhost" abläuft. Die Weiterleitung des Websockets erfolgt auf Port 9001, wo der öffentlich erreichbare Mosquitto Broker läuft.

Die HTTP-API wird über einen separaten Port (8443) ausschließlich verschlüsselt bereitgestellt. Die API selber ruft die Daten vom öffentlichen Broker auf Port 1883 ab. Auch hier wird auf Verschlüsselung verzichtet, da die Kommunikation komplett über "localhost" läuft.

Bei einer Pro+ wird auf Port 8080 ein Proxy auf die Webseite der Pro+ geöffnet. Diese beiden Ports sind komplett unabhängig von den Benutzeroberflächen und sind hier nur der Vollständigkeit halber aufgeführt.

### 2.2 Benutzeroberflächen

In der jetzigen Struktur sind mehrere separate Web-Projekte vorhanden:

1. Primärer Einstiegspunkt (Weiterleitung): `http(s)://\<IP\>/`
2. Sekundärer Einstiegspunkt (Weiterleitung): `http(s)://\<IP\>/openWB/`
3. Einstiegspunkt der Weboberfläche ("Theme-Wrapper"): `http(s)://\<IP\>/openWB/web/`
4. Einzelne Web-Themes: `http(s)://\<IP\>/openWB/web/themes/\<THEME-NAME\>/`
5. Einstiegspunkt des Displays ("Display-Wrapper"): `http(s)://\<IP\>/openWB/web/display/`
6. Einzelne Display-Themes: `http(s)://\<IP\>/openWB/web/display/themes/\<THEME-NAME\>/`
7. Einstellungen: `http(s)://\<IP\>/openWB/web/settings/`
8. Wartungsseite mit Systeminformationen: `http(s)://\<IP\>/openWB/web/maintenance/systeminfo.html`

Die Weiterleitungen unter 1. und 2. führen den Browser lediglich zu 3. Dabei ist zu beachten, dass 1. **nicht** im openWB-Verzeichnis liegt und somit auch **nicht im core Repository** vorhanden ist. Die Weiterleitung unter 2. wird in dem Installationsskript nach 1. kopiert, um das Problem zu lösen.

Der Theme-Wrapper (3.) ist der normale Einstiegspunkt für den Anwender. Es wird eine Verbindung zum Broker hergestellt, die Konfiguration des Themes empfangen und dann der Browser auf das passende Theme zu 4. weitergeleitet. Der komplette Code ist ohne ein Framework umgesetzt und teilweise aus 1.9.x übernommen und erweitert worden. Die Verbindung zum Broker richtet sich nach der aktuellen URL im Browser und wird bei HTTP unverschlüsselt, bei HTTPs verschlüsselt hergestellt.

Die einzelnen Themes (4.) arbeiten komplett unabhängig von den anderen Projekten. Das bedeutet auch, dass wichtige Links z.B. zu dem Status oder den Einstellungen in jedem Theme selbst umgesetzt werden müssen. Die Verbindung zum Broker richtet sich nach der aktuellen URL im Browser und wird bei HTTP unverschlüsselt, bei HTTPs verschlüsselt hergestellt.

Analog zu dem Theme-Wrapper funktioniert der Display-Wrapper (5.). Ein wichtiger Unterschied ist jedoch, dass keine reine Weiterleitung erfolgt, sondern das konfigurierte Display-Theme in einem Unterfenster ("iframe" mit URL zu 6.) angezeigt wird. So bleibt der Wrapper im Hintergrund aktiv und kann auf relevante Änderungen der Konfiguration (z.B. anderes Display-Theme ausgewählt) reagieren. Dieser Code hat sehr viele Überschneidungen mit dem Theme-Wrapper und wurde ebenfalls aus der 1.9.x migriert.Die Verbindung zum Broker richtet sich nach der aktuellen URL im Browser und wird bei HTTP unverschlüsselt, bei HTTPs verschlüsselt hergestellt. Das ist notwendig, da die Darstellung auch von anderen Geräten angesprochen werden kann.

Die Einstellungen (7.) sind rein optisch eine Portierung aus 1.9.x mit Anpassung auf Vue.JS als Framework. Es wird weiterhin auf Bootstrap als Layout-System gesetzt, jedoch in der veralteten Version 4.6. Das bringt einige Einschränkungen mit sich, die jedoch nur durch eine grundlegende Überarbeitung des kompletten Projektes beseitigt werden können.

Die relativ neue Wartungsseite (8.) wurde absichtlich komplett unabhängig von anderen Web-Projekten und dem Backend erstellt. Hier war "KISS" dir Voraussetzung, um auch bei Problemen mit anderen Diensten noch Daten anzeigen zu können. So muss lediglich der Webserver erreichbar sein, um die Seite aufrufen zu können. Erste Erfahrungen haben aber gezeigt, dass teilweise der Datenabruf nicht mehr funktioniert, wenn das System durch andere Prozesse ausgelastet ist.

#### 2.2.1 Web Themes

##### 2.2.1.1 Altes Standard Theme

Das "alte" Standard-Theme ist im wesentlichen eine Portierung von Code aus der 1.9.x. Sämtlicher Code ist handgeschrieben und es werden keine Frameworks verwendet. Anpassungen sind daher immer mit relativ viel Aufwand verbunden. Auch hier kommt die veraltete Bootstrap Version 4.6 zum Einsatz.

Die Verbindung zum Broker richtet sich nach der aktuellen URL im Browser und wird bei HTTP unverschlüsselt, bei HTTPs verschlüsselt hergestellt.

##### 2.2.1.2 Koala Theme

Das Koala Theme wurde von Beginn an mit aktueller Technik entwickelt. Basis ist das Quasar Framework. Dies erlaubt es z.B. aus einer Codebasis nicht nur Webseiten, sondern auch Apps für Android und iOS oder native Anwendungen für MAC/Windows/Linux zu erstellen.

Im Gegensatz zu allen anderen Web-Projekten wird im Code TypeScript anstatt reines JavaScript verwendet. Dadurch werden wesentlich mehr Hilfsfunktionen in der Entwicklungsumgebung nutzbar, welche letztendlich den Code stabiler machen.

Die Verbindung zum Broker richtet sich nach der aktuellen URL im Browser und wird bei HTTP unverschlüsselt, bei HTTPs verschlüsselt hergestellt.

##### 2.2.1.3 Colors Theme

Das Colors Theme wird von Claus "electron" aus der Community gepflegt. Wir achten jedoch darauf, dass die Verbindung zum Broker und andere Standards analog zu den offiziellen Themes eingehalten werden.

Die Verbindung zum Broker richtet sich nach der aktuellen URL im Browser und wird bei HTTP unverschlüsselt, bei HTTPs verschlüsselt hergestellt.

#### 2.2.2 Display Themes

##### 2.2.2.1 Cards Display Theme

Das Cards Theme basiert auf einer (inzwischen älteren) Version von "Inkline", einer auf Vue.js basierenden Oberflächen-Bibliothek (vergleichbar mit Bootstrap).

Die Verbindung zum Broker richtet sich nach der aktuellen URL im Browser und wird bei HTTP unverschlüsselt, bei HTTPs verschlüsselt hergestellt.

##### 2.2.2.2 Colors Display Theme

Das Colors Theme wird von Claus "electron" aus der Community gepflegt. Wir achten jedoch darauf, dass die Verbindung zum Broker und andere Standards analog zu den offiziellen Themes eingehalten werden.

Die Verbindung zum Broker richtet sich nach der aktuellen URL im Browser und wird bei HTTP unverschlüsselt, bei HTTPs verschlüsselt hergestellt.

## 3. Schnittstellen Back-/Frontend und Drittanwendungen

### 3.1 MQTT

Auf einer openWB laufen immer zwei Mosquitto Server. Einer ist nur über "localhost", also lokal laufenden Prozessen, zu erreichen. Der "externe" Server ist über eine Brücke auf Port 1884 an den lokalen gebunden. Sämtliche externen Zugriffe erfolgen immer auf den externen Broker.

#### 3.1.1 Lokaler Broker

Der lokale Broker stellt den Port 1886 (Protokoll "mqtt") ausschließlich auf "localhost" zur Verfügung. Über diesen Port sind sämtliche Topics ohne Zugangsschutz oder -regeln (ACL) les- und schreibbar. Diese Instanz wird vom Backend verwendet.

Zusätzlich wird eine Brücke zum externen Broker aufgebaut. Für diese Brücke ist dediziert festgelegt, welche Topics in welche Richtung übertragen werden.

Wenn eine weitere Brücke oder die openWB Cloud eingerichtet werden, stellt der lokale Broker auch diese Verbindungen her. Die erlaubten Topics sind in der jeweiligen Konfiguration der Brücke geregelt.

#### 3.1.2 Externer Broker

Der externe Broker stellt die Schnittstelle für sämtliche Benutzeroberflächen dar und enthält nur einen Teil der Daten des lokalen Brokers.

Über Port 1884 (mqtt, nur "localhost") kann sich der lokale Broker verbinden.

Websocket-Verbindungen können über die Ports 9001 (unverschlüsselt) und 9002 (verschlüsselt) hergestellt werden. Beide Ports erfordern keine Authentifizierung ("allow_anonymous = true") und verwenden eine ACL-Datei, um Beschränkungen im Hinblick auf lesen und schreiben zu setzen.

Analog zu den Websocket-Ports ist auch ein Zugang über das "mqtt" Protokoll (1883 unverschlüsselt, 8883 verschlüsselt) möglich. Die Sicherheitseinstellungen der beiden Ports sind analog zu den Websockets konfiguriert.

### 3.2 HTTP-API

Die HTTP-API auf Port 8443 kann nur über eine verschlüsselte Verbindung angesprochen werden. Es spricht demnach nichts dagegen, Anfragen auch in Hinsicht auf eine Authentifizierung zu erweitern. Die API selbst verwendet dann die übergebenen Anmeldedaten bei der Verbindung zum Broker. So muss die API nicht auch noch angepasst und abgesichert werden.

### 3.3 Modbus

Die Modbus Schnittstelle auf Port 1502 kann optional aktiviert werden, wenn eine openWB als secondary betrieben wird. Modbus/TCP unterstützt keine Authentifizierung und sollte daher in so einem Fall deaktiviert bleiben. Eventuell könnte die übergeordnete primary prüfen, ob Modbus auf den secondaries aktiviert ist und ggf. warnen oder die Schnittstelle eigenmächtig deaktivieren.

## 4. Leitlinien zur Entwicklung einer Umsetzung

### 4.1 Absicherung der openWB

#### 4.1.1 Grundlegende Voraussetzungen

Die hier aufgeführten Unterpunkte sind zwar Voraussetzung für eine Benutzerverwaltung, könnten aber, um die Umstellung etwas zu entzerren, bereits im Vorfeld unabhängig umgesetzt werden.

##### 4.1.1.1 Verschlüsselter Zugang

Damit Anmeldedaten nicht über das Netzwerk mitgelesen werden können, müssen sämtliche unverschlüsselten externen Zugänge (Broker, Webserver, APIs) abgeschaltet werden. Der Zugang über "localhost" (z.B. zum Broker) kann weiterhin unverschlüsselt erfolgen, falls dies noch benötigt wird und umsetzbar ist.

##### 4.1.1.2 Zertifikatsmanagement

Die verwendeten SSL-Zertifikate sind selbst signiert und können unter Umständen bei einigen Clients für Probleme sorgen, daher sollte das verwendete Zertifikat änderbar sein. Es muss eine Möglichkeit geben, den öffentlichen Teil des Zertifikates herunterzuladen, um ihn in einem Client eintragen zu können. Zusätzlich muss es die Möglichkeit geben, ein eigenes Zertifikat für den kompletten SSL-Traffic zu hinterlegen. Das beschriebene Zertifikatsmanagement wird vermutlich besonders bei größeren Installationen von Bedeutung sein.

##### 4.1.1.3 Hostname und IP anpassbar

Im Zusammenhang mit Zertifikaten ist es wichtig, dass der Hostname zum Zertifikat passt. Ebenfalls kann eine IP Teil des Zertifikats sein. Folglich sollten beide Einstellungen anpassbar sein.

Die IP des "Plug'n'Play" Netzwerkes (Standard `192.168.193.250`) sollte in diesem Zuge ebenfalls konfigurierbar umgesetzt werden, damit es nicht potentiell zu Konflikten kommt bzw. ein Adresskonflikt durch Anpassung behoben werden kann.

#### 4.1.2 Rechtemanagement

Für den Mosquitto Broker gibt es das [Dynamic Security Plugin](https://mosquitto.org/documentation/dynamic-security/). Dieses erlaubt eine sehr feine Rechteverwaltung auf Basis von Clients, Rollen und ACLs. Die komplette Konfiguration erfolgt ebenfalls zur Laufzeit per MQTT. Es wird empfohlen, dafür das Programm `mosquitto_ctrl` auf der Kommandozeile zu verwenden, es ist aber auch möglich, Einstellungen direkt über Topics zu setzen.

#### 4.1.3 Zurücksetzen eines Kennwortes

Es muss zwingend für den Administrator/Hauptbenutzer die Möglichkeit geben, den Zugang bei einem vergessenen Kennwort wieder herzustellen. Im einfachsten Fall könnte das, wie bei vielen Lösungen üblich, über eine hinterlegte E-Mail Adresse erfolgen, an die ein Code gesendet wird.

Im Besten Fall lässt sich diese Option pro angelegtem Benutzer (de-)aktivieren.

### 4.2 Startseite

Wenn die openWB im Browser aufgerufen wird, sollte als erstes eine Anmeldemaske erscheinen. So ist sichergestellt, dass unbefugte keine Möglichkeit haben, Einstellungen zu verändern und in eventuell andere Ladevorgänge einzugreifen. Das bedeutet auch, dass mindestens die URL `http(s)://\<IP\>/openWB/web/` durch die Anmeldeseite abgefangen werden muss.

Um abwärtskompatibel zu bleiben, sollte der Pfad `/openWB/web/` beibehalten werden, auch wenn er eigentlich keinen Sinn mehr macht (Überbleibsel aus 1.x). Die beiden reinen Weiterleitungen (Punkte 1. und 2. in Abschnitt 2.2) können demnach erhalten bleiben.

### 4.3 Veralteten Code entfernen

Der unter 2.2 aufgeführte "Theme-Wrapper" (Punkt 3.) muss im Zuge einer Benutzerverwaltung komplett überarbeitet werden, da dieser Pfad von der neuen Anmeldeseite verwendet wird (siehe 3.1). Ohne eine vorherige Anmeldung darf kein Theme angezeigt werden. Daher bietet es sich an, diese Funktionalität in das neue Projekt zu integrieren.

### 4.4 Einheitliches Menü für alle Themes

Oben wurde angesprochen, dass jedes Theme für die Links zu Status, Einstellungen etc. selbst verantwortlich ist. Es muss also in jedem Theme ein gewisser Anteil Code zwingend enthalten sein. Dabei stelle ich mir die Frage, ob das nicht einheitlich gelöst werden kann.

| ![Bereiche eines Themes - Koala](<Theme-Bereiche.png>) |
|:--:|
| *Abbildung 1: Die farblich markierten Bereiche im Koala Theme zeigen, welche Funktionen einheitlich umgesetzt werden sollten (grün) und welche individuell vom Theme gestaltet werden (gelb).* |

Am Beispiel des Koala Themes habe ich in Abbildung 1 zwei Bereiche eingefärbt. Grün hinterlegt ist die Funktionalität, welche in jedem Theme aktuell selbst umgesetzt werden muss. Der gelbe Bereich hingegen ist individuell vom jeweiligen Theme gestaltet.

Wie zu Punkt 3. in 2.2 erläutert, leitet der jetzige Theme-Wrapper den Browser direkt auf das konfigurierte Theme weiter. Außer dem Theme ist also nichts in diesem Tab aktiv. Der Display-Wrapper (Punkt 5. in 2.2) hingegen zeigt das konfigurierte Theme in einem separaten Bereich an und bleibt selber im Hintergrund aktiv. Dieses Verhalten kann auch bei den Web-Themes genutzt werden.

Bleibt das Login-System (bzw. vormals der Wrapper) im Hintergrund aktiv, dann kann es sich auch um die Darstellung der Links kümmern. Das ausgewählte Theme wird dann im gelben Bereich eingeblendet und muss kein eigenes Menü mit Links mehr erzeugen. So ist außerdem sichergestellt, dass alle gewünschten Links in allen Themes vorhanden sind. Eine Anpassung muss dann nur einmal erfolgen, anstatt in allen Themes umgesetzt zu werden.

### 4.5 Integration der Einstellungen

Wenn bereits das Menü vereinheitlicht wird (3.3), dann bietet es sich auch an, die Einstellungen auch in den gelben Bereich (siehe Abbildung 1) zu integrieren. So bleibt das Bedienkonzept konsistent und es muss das Menüsystem nicht erneut in den Einstellungen umgesetzt werden.

### 4.6 Offene Punkte

#### 4.6.1 Betrieb ohne Anmeldung

Zu klären wäre noch, ob optional das alte Verhalten ohne Anmeldung zu ermöglichen ist. Dazu könnte ein Benutzer angelegt werden, mit dem sich das Frontend automatisch anmeldet. Diesem Benutzer können beispielsweise Rechte eingeräumt werden, die eine rudimentäre Bedienung ermöglichen bis hin zu Vollzugriff, um weiterhin komplett ohne Anmeldung arbeiten zu können.

#### 4.6.2 Login-System optisch an Theme anpassen

Damit es keinen harten optischen Kontrast zwischen dem einheitlichen Menü und dem ausgewählten Theme gibt, sollte sich die Darstellung des Menüs in gewisser Weise an das Theme anpassen können. Im einfachsten Fall werden vom Theme Farben für Schrift und Hintergrund für den hellen und dunklen Modus vorgegeben.

Weitere Möglichkeiten wie z.B. die Erweiterung des Menüs um spezifische Punkte sind ebenfalls denkbar, die Umsetzung muss jedoch noch geprüft werden.

#### 4.6.3 Display

Der Display-Wrapper sowie die dadurch eingebundenen Display Themes müssen sich bei aktivierter Benutzerverwaltung ebenfalls in irgendeiner Weise anmelden. Besonders bei größeren Installationen mit verschiedenen Benutzerrollen je Wallbox (z.B. WEGs), stellt dies eine größere Herausforderung dar. Eventuell könnte der Zugriff über IPs geregelt werden.

#### 4.6.4 JSON Daten

In manchen Situationen kann es sinnvoll sein, dass ein Client nur einen Teil eines größeren JSON Topics schreiben (ggf. auch lesen?) kann. Ein Fall wären z.B. die Lade-Profile, wo vermutlich "Priorität" und "Standard nach Abstecken" für einen normalen Anwender nicht änderbar sein sollten, andere Daten wie "Lademodus" hingegen schon.

Es müsste evaluiert werden, welche JSON Objekte im Hinblick auf ein Rechtemanagement aufzuteilen sind und dafür eine Lösung geschaffen werden. Primäres Ziel sollte es sein, dass nicht auch noch im Backend eine Benutzerverwaltung implementiert werden muss, sondern ausschließlich mit dem Rechtemanagement im Broker gearbeitet werden kann. Ansonsten müssten zwei Bereiche immer synchron gehalten werden, was früher oder später vermutlich zu Problemen führen wird.
