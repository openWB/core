_Einstellungen -> Konfiguration -> Fahrzeuge -> Lade-Profile_

Unter den Lade-Profilen werden die Einstellungen für das Ladeprofil verwaltet. Die Einstellungen auf der Hauptseite werden aus diesem Profil geladen und dorthin geschrieben. Ist nur ein Fahrzeug vorhanden, so wird in den meisten Fällen nur das Standard-Ladeprofil benötigt. Ausgenommen hiervon ist, wenn per RFID-Tag Ladevorgaben ausgewählt werden.

In den fahrzeugspezifischen Einstellungen wird ein Ladeprofil einem Fahrzeug zugeordnet. Werden zwei Fahrzeuge geladen, empfiehlt es sich dazu ein zweites Ladeprofil anzulegen.

### Temporäre Ladeprofile (ab Version 2.1.7)
Anpassungen am Ladeprofil, die über die Hauptseite (Web-Themes) oder ein Display (Display-Themes) vorgenommen werden, sind temporär. Die Lade-Profile müssen direkt in den Einstellungen bearbeitet werden.
Die temporären Einstellungen werden mit dem Ladeprofil aus den Einstellungen überschrieben, wenn 
... abgesteckt wird.
... das Fahrzeug gewechselt wird. Das Lade-Profil des neuen Fahrzeugs wird geladen.
... das Ladeprofil geändert wird und kein Fahrzeug angesteckt ist. Ist ein Fahrzeug angesteckt, gelten die temporären Einstellungen bis zum Abstecken und werden dann durch das Ladeprofil überschrieben.