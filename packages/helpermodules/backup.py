import json
import pathlib
import tarfile
import os.path

from helpermodules import timecheck
from helpermodules.broker import InternalBroker


class Backup():
    def __init__(self) -> None:
        self.all_received_topics = []
        InternalBroker("create_backup", self.on_connect, self.on_message)

        backup_folder = self._get_openwb_folder() / "data" / "backup"
        backup_folder.mkdir(mode=0o755, parents=True, exist_ok=True)
        topic_file = backup_folder / f"topics_{timecheck.create_timestamp_unix()}.json"
        with open(topic_file, "w") as jsonFile:
            json.dump(self.all_received_topics, jsonFile)
        with tarfile.open(backup_folder / f"openWB_backup_{timecheck.create_timestamp_unix()}.tar.gz", "w:gz") as tar:
            tar.add(self._get_openwb_folder(), arcname=os.path.basename(self._get_openwb_folder()))
        pathlib.Path.unlink(topic_file)

    def _get_openwb_folder(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2]

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("openWB/vehicle/#", 2)
        client.subscribe("openWB/chargepoint/#", 2)
        client.subscribe("openWB/pv/#", 2)
        client.subscribe("openWB/bat/#", 2)
        client.subscribe("openWB/general/#", 2)
        client.subscribe("openWB/optional/#", 2)
        client.subscribe("openWB/counter/#", 2)
        client.subscribe("openWB/system/#", 2)

    def on_message(self, client, userdata, msg):
        self.all_received_topics.append({msg.topic: json.loads(str(msg.payload.decode("utf-8")))})
