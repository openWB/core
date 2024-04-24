Dieses SOC-Modul ist von der javascipt Implementierung des smartEQ Adapters von iobroker und der Implementierung des mbapi in home assistant inspiriert.
Credits:
https://github.com/TA2k/ioBroker.smart-eq
https://github.com/ReneNulschDE/mbapi2020

requirements: bs4, pkce, protobuf, websocket-client

Dieses File:
README.txt

Files des SOC-Modul:
api.py
config.py
__init__.py
soc.py
socutils.py

Generierte files des protobuf (im folder proto):
  acp_pb2.py
  client_pb2.py
  cluster_pb2.py
  eventpush_pb2.py
  gogo_pb2.py
  protos_pb2.py
  service_activation_pb2.py
  user_events_pb2.py
  vehicleapi_pb2.py
  vehicle_commands_pb2.py
  vehicle_events_pb2.py
  vin_events_pb2.py

Anmerkung: diese Files sind generiert und leider nicht "flake8 clean".
Das Generierungs-Script macht nur einige Änderungen an den Pfaden damit dioe Dateien im 
Context des SOC-Moduls funktionieren.

Script zur (Re-)Generierung der Protobuf files (im folder utils):
  generateProtobuf.sh
