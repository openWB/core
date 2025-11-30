#!/usr/bin/env python3
from pathlib import Path
import logging
import subprocess
from threading import Thread

from control import data
from dataclass_utils._dataclass_asdict import asdict
from helpermodules import timecheck
from helpermodules.broker import BrokerClient
from helpermodules.pub import pub_single
from helpermodules.utils.run_command import run_command
from helpermodules.utils._thread_handler import is_thread_alive, thread_handler
from helpermodules.utils.topic_parser import decode_payload
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import IoState
from modules.common.configurable_io import ConfigurableIo
from modules.io_devices.eebus.config import AnalogInputMapping, CertInfo, DigitalInputMapping, Eebus

log = logging.getLogger(__name__)
control_command_log = logging.getLogger("steuve_control_command")

cert_path = f"{Path(__file__).resolve().parents[4]}/data/config/eebus/certs"

# Fehlercodes des eebus clients
# 1: "FEHLER: Zu wenig Argumente! Erwartet: <port> <remoteski> <certfile> <keyfile> <logpath>"
# 2: "FEHLER: Zertifikat oder Key ungültig"
# 4: "FEHLER: Port ungültig"
# 5: "FEHLER: MQTT nicht erreichbar"
# 6: "FEHLER: Keine Verbindung zur Steuerbox (Controlbox) aufgebaut!"
# 7: "FEHLER: Remote SKI leer!"
# 8: "FEHLER: Der entfernte Dienst hat das Vertrauen verweigert."


def create_io(config: Eebus):
    received_topics = {}
    broker = None
    thread_exception = None  # Shared state für Thread-Exceptions

    def run_eebus():
        def run():
            nonlocal thread_exception
            try:
                log.debug(f"Starte EEbus-Client für Steuerbox mit ID {config.id} und "
                          f"SKI {config.configuration.remote_ski}")
                subprocess.run(
                    [f"{Path(__file__).resolve().parents[0]}/eebus_hems_client",
                        str(config.configuration.port),
                        config.configuration.remote_ski,
                        f"{cert_path}/hems-cert-{config.id}.pem",
                        f"{cert_path}/hems-key-{config.id}.pem",
                        str(config.id),
                        f"{Path(__file__).resolve().parents[4]}/ramdisk/eebus_hems_client.log"],

                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                if e.returncode == 2:
                    msg = ("Zertifikat oder Key ungültig. Wenn das Zertifikat abgelaufen ist, bitte in "
                           "den Einstellungen ein neues Zertifikat generieren und den SKI beim VNB "
                           "akutalisieren.")
                    control_command_log.error(msg)
                    thread_exception = ValueError(msg)
                else:
                    control_command_log.error(f"Fehlercode: {e.returncode}, Fehler: {e.stderr}")
                    thread_exception = ValueError(f"Fehlercode: {e.returncode}, Fehler: {e.stderr}")
            except Exception as e:
                control_command_log.error(f"Fehler im EEbus-Client: {e}")
                thread_exception = e
        thread_handler(Thread(
            target=run,
            args=(),
            name="eebus_binary"))

    def read():
        nonlocal broker
        nonlocal received_topics
        nonlocal thread_exception

        if is_thread_alive("eebus_binary") is False:
            run_eebus()
            if thread_exception is not None:
                exception_to_raise = thread_exception
                thread_exception = None
                raise exception_to_raise
        broker.start_finite_loop()
        log.debug(f"Empfange MQTT Daten für EEBus {config.id}: {received_topics}")
        io_state = IoState()
        io_state.analog_input = getattr(io_state, "analog_input", None) or {}
        io_state.analog_output = getattr(io_state, "analog_output", None) or {}
        io_state.digital_input = getattr(io_state, "digital_input", None) or {}
        io_state.digital_output = getattr(io_state, "digital_output", None) or {}

        def process_payload(payload, value_key, msg_counter_key, active_key, end_time_key):
            io_state.analog_input.update({
                value_key: payload["limit"],
                msg_counter_key: payload["msgCounter"],
                end_time_key: timecheck.create_timestamp() + timecheck.parse_iso8601_duration(payload["duration"])
            })
            io_state.digital_input.update({active_key: payload["isLimitActive"]})

        if received_topics.get(f"openWB/eebus/{config.id}/get/fault_state") != 0:
            raise Exception(received_topics[f"openWB/eebus/{config.id}/get/fault_str"])

        if received_topics.get(f"openWB/eebus/{config.id}/get/lpc"):
            process_payload(
                received_topics[f"openWB/eebus/{config.id}/get/lpc"],
                AnalogInputMapping.LPC_VALUE.name,
                AnalogInputMapping.LPC_MSG_COUNTER.name,
                DigitalInputMapping.LPC_ACTIVE.name,
                AnalogInputMapping.LPC_END_TIME.name
            )
        if received_topics.get(f"openWB/eebus/{config.id}/get/lpp"):
            process_payload(
                received_topics[f"openWB/eebus/{config.id}/get/lpp"],
                AnalogInputMapping.LPP_VALUE.name,
                AnalogInputMapping.LPP_MSG_COUNTER.name,
                DigitalInputMapping.LPP_ACTIVE.name,
                AnalogInputMapping.LPP_END_TIME.name
            )

        return io_state

    def initializer():
        nonlocal broker
        nonlocal received_topics
        Path(f"{Path(__file__).resolve().parents[4]}/ramdisk/eebus_hems_client.log").touch(exist_ok=True)
        run_eebus()

        def on_connect(client, userdata, flags, rc):
            client.subscribe(f"openWB/eebus/{config.id}/#")

        def on_message(client, userdata, message):
            received_topics.update({message.topic: decode_payload(message.payload)})

        received_topics = {}
        broker = BrokerClient(f"subscribeMqttEebus{config.id}",
                              on_connect, on_message)

    return ConfigurableIo(config=config, component_reader=read, component_writer=lambda: None, initializer=initializer)


device_descriptor = DeviceDescriptor(configuration_factory=Eebus)


def create_pub_cert_ski(id: int):
    Path(cert_path).mkdir(parents=True, exist_ok=True)
    run_command([
        "openssl", "req", "-x509",
        "-newkey", "rsa:4096", "-keyout", f"{cert_path}/hems-key-{id}.pem",
        "-out", f"{cert_path}/hems-cert-{id}.pem",
        "-days", "365", "-nodes",
        "-subj", "/CN=HEMS/C=DE/O=openWB GmbH"
    ])

    output = run_command([
        "openssl", "x509", "-in", f"{cert_path}/hems-cert-{id}.pem", "-noout", "-text"
    ])
    cert_info = CertInfo()
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if "Subject Key Identifier" in line:
            cert_info.client_ski = lines[i+1].strip().replace(":", "")
        elif "Not Before:" in line:
            cert_info.not_before = line.split("Not Before: ")[1].strip()
        elif "Not After :" in line:
            cert_info.not_after = line.split("Not After : ")[1].strip()
        elif line.strip().startswith("Issuer:"):
            cert_info.issuer = line.strip()[len("Issuer: "):].strip()
        elif line.strip().startswith("Subject:"):
            cert_info.subject = line.strip()[len("Subject: "):].strip()
    if "" == cert_info.client_ski:
        raise ValueError("SKI nicht gefunden")
    config: Eebus = data.data.system_data[f"io{id}"].config
    config.configuration.cert_info = cert_info
    with open(f"{cert_path}/ski-{id}", "w") as ski_file:
        ski_file.write(cert_info.client_ski)
    pub_single(f"openWB/set/system/io/{config.id}/config", asdict(config))
