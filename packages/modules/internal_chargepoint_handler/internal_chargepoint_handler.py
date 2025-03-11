#!/usr/bin/python
import copy
import logging
import threading
import time
from typing import Optional
from helpermodules import timecheck
from helpermodules import pub

from helpermodules.pub import Pub, pub_single
from helpermodules.subdata import SubData
from modules.chargepoints.internal_openwb.config import InternalChargepointMode
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store._util import get_rounding_function_by_digits
from modules.common.component_state import ChargepointState
from modules.internal_chargepoint_handler import chargepoint_module
from modules.internal_chargepoint_handler.clients import ClientHandler, client_factory
from modules.internal_chargepoint_handler.pro_plus import ProPlus
from modules.internal_chargepoint_handler.socket import Socket
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import (
    GlobalHandlerData, InternalChargepoint, InternalChargepointData, RfidData)
log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class UpdateValues:
    def __init__(self,
                 local_charge_point_num: int,
                 parent_ip: Optional[str],
                 parent_cp: str,
                 hierarchy_id: int) -> None:
        self.local_charge_point_num_str = str(local_charge_point_num)
        self.old_chargepoint_state = None
        self.parent_ip = parent_ip
        self.parent_cp = parent_cp
        self.hierarchy_id = hierarchy_id

    def update_values(self, chargepoint_state: ChargepointState, heartbeat_expired: bool) -> None:
        if self.parent_ip is not None:
            if self.old_chargepoint_state:
                # iterate over counter state
                vars_old_counter_state = vars(self.old_chargepoint_state)
                for key, value in vars(chargepoint_state).items():
                    # Zählerstatus immer veröffentlichen für Ladelog-Einträge
                    if value != vars_old_counter_state[key] or key == "imported":
                        self._pub_values_to_2(key, value)
            else:
                # Bei Neustart alles veröffentlichen
                for key, value in vars(chargepoint_state).items():
                    self._pub_values_to_2(key, value)
            if heartbeat_expired is False:
                # Nur wenn eine Verbindung zum Master besteht, die veröffentlichten Werte speichern.
                self.old_chargepoint_state = chargepoint_state

    def _pub_values_to_2(self, topic: str, value) -> None:
        rounding = get_rounding_function_by_digits(2)
        # fix rfid default value
        if topic == "rfid" and value == "0":
            value = None
        if isinstance(value, (str, bool, type(None))):
            payload = value
        else:
            # qos 2 reicht nicht, da die Daten zwar auf dem Broker ankommen, aber nicht verarbeitet werden.
            if isinstance(value, list):
                payload = [rounding(v) for v in value]
            else:
                payload = rounding(value)
        pub_single(f"openWB/set/chargepoint/{self.parent_cp}/get/{topic}", payload=payload, hostname=self.parent_ip)
        if self.parent_ip != "localhost":
            pub_single(f"openWB/set/chargepoint/{self.hierarchy_id}/get/state_str",
                       payload="Statusmeldungen bitte auf der Primary-openWB einsehen.")


class UpdateState:
    def __init__(self, cp_module: chargepoint_module.ChargepointModule, hierarchy_id: int) -> None:
        self.old_phases_to_use = 0
        self.old_set_current = 0
        self.phase_switch_thread = None  # type: Optional[threading.Thread]
        self.cp_interruption_thread = None  # type: Optional[threading.Thread]
        self.actor_cooldown_thread = None  # type: Optional[threading.Thread]
        self.cp_module = cp_module
        self.hierarchy_id = hierarchy_id

    def update_state(self, data: InternalChargepoint, heartbeat_expired: bool) -> None:
        if heartbeat_expired:
            set_current = 0
        else:
            set_current = data.set_current
        log.debug(f"Values from parentWB: {data}")

        if self.phase_switch_thread:
            if self.phase_switch_thread.is_alive():
                log.debug("Thread zur Phasenumschaltung an LP"+str(self.cp_module.local_charge_point_num) +
                          " noch aktiv. Es muss erst gewartet werden, bis die Phasenumschaltung abgeschlossen ist.")
                return
        if self.cp_interruption_thread:
            if self.cp_interruption_thread.is_alive():
                log.debug("Thread zur CP-Unterbrechung an LP"+str(self.cp_module.local_charge_point_num) +
                          " noch aktiv. Es muss erst gewartet werden, bis die CP-Unterbrechung abgeschlossen ist.")
                return
        self.cp_module.set_current(set_current)
        pub_single(f"openWB/set/chargepoint/{self.hierarchy_id}/set/current", payload=set_current)
        if data.trigger_phase_switch:
            log.debug("Switch Phases from "+str(self.old_phases_to_use) + " to " + str(data.phases_to_use))
            self.__thread_phase_switch(data.phases_to_use)
            pub.pub_single(
                f"openWB/set/internal_chargepoint/{self.cp_module.local_charge_point_num}/data/trigger_phase_switch",
                False)

        if data.cp_interruption_duration > 0:
            self.__thread_cp_interruption(data.cp_interruption_duration)

    def __thread_phase_switch(self, phases_to_use: int) -> None:
        self.phase_switch_thread = threading.Thread(
            target=self.cp_module.perform_phase_switch, args=(phases_to_use, 5),
            name=f"perform phase switch {self.cp_module.local_charge_point_num}")
        self.phase_switch_thread.start()
        log.debug("Thread zur Phasenumschaltung an LP"+str(self.cp_module.local_charge_point_num)+" gestartet.")

    def __thread_cp_interruption(self, duration: int) -> None:
        self.cp_interruption_thread = threading.Thread(
            target=self.cp_module.perform_cp_interruption, args=(duration,),
            name=f"perform cp interruption cp{self.cp_module.local_charge_point_num}")
        self.cp_interruption_thread.start()
        log.debug("Thread zur CP-Unterbrechung an LP"+str(self.cp_module.local_charge_point_num)+" gestartet.")
        Pub().pub(
            f"openWB/internal_chargepoint/{self.cp_module.local_charge_point_num}/data/cp_interruption_duration", 0)


class InternalChargepointHandler:
    def __init__(self,
                 mode: InternalChargepointMode,
                 global_data: GlobalHandlerData,
                 parent_cp0: str,
                 hierarchy_id_cp0: int,
                 parent_cp1: Optional[str],
                 hierarchy_id_cp1: Optional[int],
                 event_start: threading.Event,
                 event_stop: threading.Event) -> None:
        log.debug(f"Init internal chargepoint as {mode}")
        self.event_start = event_start
        self.event_stop = event_stop
        self.heartbeat = False
        self.fault_state_info_cp0 = FaultState(
            ComponentInfo(hierarchy_id_cp0, "Interner Ladepunkt 0", "chargepoint", parent_id=parent_cp0,
                          parent_hostname=global_data.parent_ip))
        fault_state_info_cp1 = FaultState(
            ComponentInfo(hierarchy_id_cp1, "Interner Ladepunkt 1", "chargepoint", parent_id=parent_cp1,
                          parent_hostname=global_data.parent_ip))
        with SingleComponentUpdateContext(self.fault_state_info_cp0, reraise=True):
            self.init_gpio()
        try:
            with SingleComponentUpdateContext(self.fault_state_info_cp0, reraise=True):
                # Allgemeine Fehlermeldungen an LP 1:
                if mode == InternalChargepointMode.PRO_PLUS.value:
                    self.cp0_client_handler = None
                else:
                    self.cp0_client_handler = client_factory(0, self.fault_state_info_cp0)
                self.cp0 = HandlerChargepoint(self.cp0_client_handler, 0, mode,
                                              global_data, parent_cp0, hierarchy_id_cp0)
        except Exception:
            self.cp0_client_handler = None
            self.cp0 = None
        try:
            if mode == InternalChargepointMode.DUO.value:
                with SingleComponentUpdateContext(fault_state_info_cp1, reraise=True):
                    log.debug("Zweiter Ladepunkt für Duo konfiguriert.")
                    self.cp1_client_handler = client_factory(1, fault_state_info_cp1, self.cp0_client_handler)
                    self.cp1 = HandlerChargepoint(self.cp1_client_handler, 1, mode,
                                                  global_data, parent_cp1, hierarchy_id_cp1)
            else:
                self.cp1 = None
                self.cp1_client_handler = None
        except Exception:
            self.cp1 = None
            self.cp1_client_handler = None

    def init_gpio(self) -> None:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(37, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(22, GPIO.OUT)
        GPIO.setup(29, GPIO.OUT)
        GPIO.setup(11, GPIO.OUT)
        GPIO.setup(15, GPIO.OUT)
        # GPIOs for socket
        GPIO.setup(23, GPIO.OUT)
        GPIO.setup(26, GPIO.OUT)
        GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def loop(self) -> None:
        def _loop():
            while True:
                if self.event_stop.is_set():
                    break
                log.debug("***Start***")
                data = copy.deepcopy(SubData.internal_chargepoint_data)
                log.debug(data)
                log.setLevel(SubData.system_data["system"].data["debug_level"])
                heartbeat_cp0, heartbeat_cp1 = True, True
                if self.cp0:
                    heartbeat_cp0 = self.cp0.update(data["global_data"], data["cp0"].data, data["rfid_data"])
                if self.cp1:
                    heartbeat_cp1 = self.cp1.update(data["global_data"], data["cp1"].data, data["rfid_data"])
                self.heartbeat = True if heartbeat_cp0 and heartbeat_cp1 else False
                time.sleep(1.1)
        with SingleComponentUpdateContext(self.fault_state_info_cp0, update_always=False):
            # Allgemeine Fehlermeldungen an LP 1
            if self.cp0.mode == InternalChargepointMode.PRO_PLUS.value:
                _loop()
            elif self.cp0_client_handler is None and self.cp1_client_handler is None:
                log.error("Kein ClientHandler vorhanden. Beende.")
            elif self.cp0_client_handler is not None and self.cp1_client_handler is None:
                with self.cp0_client_handler.client:
                    _loop()
            elif self.cp0_client_handler is None and self.cp1_client_handler is not None:
                with self.cp1_client_handler.client:
                    _loop()
            elif self.cp0_client_handler.client == self.cp1_client_handler.client:
                with self.cp0_client_handler.client:
                    _loop()
            elif self.cp0_client_handler is not None and self.cp1_client_handler is not None:
                with self.cp0_client_handler.client:
                    with self.cp1_client_handler.client:
                        _loop()
            else:
                log.error("Kein ClientHandler vorhanden. Beende.")


class HandlerChargepoint:
    def __init__(self,
                 client_handler: Optional[ClientHandler],
                 local_charge_point_num: int,
                 mode: InternalChargepointMode,
                 global_data: GlobalHandlerData,
                 parent_cp: str,
                 hierarchy_id: int) -> None:
        self.local_charge_point_num = local_charge_point_num
        self.mode = mode
        if local_charge_point_num == 0:
            if mode == InternalChargepointMode.SOCKET.value:
                self.module = Socket(local_charge_point_num, client_handler,
                                     global_data.parent_ip, parent_cp, hierarchy_id)
            elif mode == InternalChargepointMode.PRO_PLUS.value:
                self.module = ProPlus(local_charge_point_num, global_data.parent_ip, parent_cp, hierarchy_id)
            else:
                self.module = chargepoint_module.ChargepointModule(
                    local_charge_point_num, client_handler, global_data.parent_ip, parent_cp, hierarchy_id)
        else:
            self.module = chargepoint_module.ChargepointModule(
                local_charge_point_num, client_handler, global_data.parent_ip, parent_cp, hierarchy_id)
        with SingleComponentUpdateContext(self.module.fault_state):
            self.update_values = UpdateValues(local_charge_point_num, global_data.parent_ip, parent_cp, hierarchy_id)
            self.update_state = UpdateState(self.module, hierarchy_id)
            self.old_plug_state = False

    def update(self, global_data: GlobalHandlerData, data: InternalChargepointData, rfid_data: RfidData) -> bool:
        def __thread_active(thread: Optional[threading.Thread]) -> bool:
            if thread:
                return thread.is_alive()
            else:
                return False
        with SingleComponentUpdateContext(self.module.fault_state):
            if self.local_charge_point_num == 1:
                time.sleep(0.1)
            phase_switch_cp_active = __thread_active(self.update_state.cp_interruption_thread) or __thread_active(
                self.update_state.phase_switch_thread)
            state = self.module.get_values(phase_switch_cp_active, rfid_data.last_tag)
            log.debug("Published plug state "+str(state.plug_state))
            heartbeat_expired = self._check_heartbeat_expired(global_data.heartbeat)
            if global_data.parent_ip is not None:
                self.update_values.update_values(state, heartbeat_expired)
            self.update_state.update_state(data, heartbeat_expired)
            return True
        return False

    def _check_heartbeat_expired(self, heartbeat) -> bool:
        if heartbeat+80 < timecheck.create_timestamp():
            log.error(f"Heartbeat Fehler seit {timecheck.create_timestamp()-heartbeat}"
                      "s keine Verbindung. Stoppe Ladung.")
            return True
        else:
            return False


class GeneralInternalChargepointHandler:
    def __init__(self) -> None:
        self.event_stop = threading.Event()
        self.event_start = threading.Event()

    def handler(self):
        while True:
            try:
                self.event_start.wait()
                self.event_start.clear()
                self.event_stop.clear()
                # wait a moment to subscribe all data
                time.sleep(2)
                data = copy.deepcopy(SubData.internal_chargepoint_data)
                hierarchy_id_cp0 = None
                hierarchy_id_cp1 = None
                for cp in SubData.cp_data.values():
                    if cp.chargepoint.chargepoint_module.config.type == "internal_openwb":
                        mode = cp.chargepoint.chargepoint_module.config.configuration.mode
                        if cp.chargepoint.chargepoint_module.config.configuration.duo_num == 0:
                            hierarchy_id_cp0 = cp.chargepoint.num
                        else:
                            hierarchy_id_cp1 = cp.chargepoint.num

                try:
                    self.internal_chargepoint_handler = InternalChargepointHandler(
                        mode,
                        data["global_data"],
                        data["cp0"].data.parent_cp,
                        hierarchy_id_cp0,
                        data["cp1"].data.parent_cp,
                        hierarchy_id_cp1,
                        self.event_start,
                        self.event_stop)
                    self.internal_chargepoint_handler.loop()
                except UnboundLocalError:
                    log.debug("Kein interner Ladepunkt konfiguriert.")
            except Exception:
                log.exception("Fehler im internem Ladepunkt")
