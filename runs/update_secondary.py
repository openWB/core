#!/usr/bin/env python3
import sys
sys.path.append("/var/www/html/openWB/packages")
try:
    from helpermodules import pub
except Exception as e:
    # Durch try-except werden die Imports vom Formatierer nicht an den Dateianfang geschoben.
    print(e)

secondary_ip = sys.argv[1]
print("IP der Secondary: "+secondary_ip)

pub.pub_single("openWB/set/command/primary/todo",
               {"command": "systemUpdate", "data": {}},
               hostname=secondary_ip)

print("Update Befehl an Secondary gesendet.")
