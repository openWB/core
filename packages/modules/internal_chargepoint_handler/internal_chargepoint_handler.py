#!/usr/bin/python
from contextlib import ExitStack
import copy
import logging
from threading import Event, Thread
import time
from typing import Optional
from helpermodules import timecheck

from helpermodules import pub
from helpermodules.logger import ModifyLoglevelContext, clear_in_memory_log_handler
from helpermodules.pub import Pub
from helpermodules.subdata import SubData
from modules.chargepoints.internal_openwb.config import InternalChargepointMode
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusSerialClient_
from modules.common.serial_modbus_devices import BUS_SOURCES, get_serial_modbus_devices
from modules.internal_chargepoint_handler import chargepoint_module
from modules.internal_chargepoint_handler.clients import ClientHandler, client_factory, get_modbus_client
from modules.internal_chargepoint_handler.hardware_definition import WALLBOX_SOCKET_METERS
from modules.internal_chargepoint_handler.pro_plus import ProPlus
from modules.internal_chargepoint_handler.socket import Socket
from modules.internal_chargepoint_handler.wallbox_socket import WallboxSocketModule
from modules.internal_chargepoint_handler.wallbox_socket_config import WallboxSocket, WallboxSocketData
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import (
    GlobalHandlerData, InternalChargepoint, InternalChargepointData, RfidData)
log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class UpdateState:
    def __init__(self, cp_module: chargepoint_module.ChargepointModule, hierarchy_id: int) -> None:
        self.old_phases_to_use = 0
        self.old_set_current = 0
        self.phase_switch_thread = None  # type: Optional[Thread]
        self.cp_interruption_thread = None  # type: Optional[Thread]
        self.actor_cooldown_thread = None  # type: Optional[Thread]
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
        Pub().pub(f"openWB/set/chargepoint/{self.hierarchy_id}/set/current", payload=set_current)
        if data.trigger_phase_switch:
            log.debug("Switch Phases from "+str(self.old_phases_to_use) + " to " + str(data.phases_to_use))
            self.__thread_phase_switch(data.phases_to_use)
            Pub().pub(
                f"openWB/set/internal_chargepoint/{self.cp_module.local_charge_point_num}/data/trigger_phase_switch",
                False)

        if data.cp_interruption_duration > 0:
            self.__thread_cp_interruption(data.cp_interruption_duration)

    def __thread_phase_switch(self, phases_to_use: int) -> None:
        self.phase_switch_thread = Thread(
            target=self.cp_module.perform_phase_switch, args=(phases_to_use,),
            name=f"perform phase switch {self.cp_module.local_charge_point_num}")
        self.phase_switch_thread.start()
        log.debug("Thread zur Phasenumschaltung an LP"+str(self.cp_module.local_charge_point_num)+" gestartet.")

    def __thread_cp_interruption(self, duration: int) -> None:
        self.cp_interruption_thread = Thread(
            target=self.cp_module.perform_cp_interruption, args=(duration,),
            name=f"perform cp interruption cp{self.cp_module.local_charge_point_num}")
        self.cp_interruption_thread.start()
        log.debug("Thread zur CP-Unterbrechung an LP"+str(self.cp_module.local_charge_point_num)+" gestartet.")
        Pub().pub(
            f"openWB/internal_chargepoint/{self.cp_module.local_charge_point_num}/data/cp_interruption_duration", 0)


class UpdateWallboxSocketState:
    def __init__(self, wallbox_socket_module: WallboxSocketModule) -> None:
        self.module = wallbox_socket_module

    def update_state(self, data: WallboxSocketData, heartbeat_expired: bool) -> None:
        if not data.set_state or heartbeat_expired:
            self.module.set_state(False)
        else:
            self.module.set_state(True)


class InternalChargepointHandler:
    def __init__(self,
                 mode: InternalChargepointMode,
                 global_data: GlobalHandlerData,
                 parent_cp0: InternalChargepoint,
                 hierarchy_id_cp0: int,
                 parent_cp1: Optional[InternalChargepoint],
                 hierarchy_id_cp1: Optional[int],
                 parent_wallbox_socket: WallboxSocket,
                 event_start: Event,
                 event_stop: Event) -> None:
        log.debug(f"Init internal chargepoint as {mode}")
        self.event_start = event_start
        self.event_stop = event_stop
        self.heartbeat = False
        self.fault_state_info_cp0 = FaultState(
            ComponentInfo(0, "Interner Ladepunkt 0", "internal_chargepoint", hierarchy_id=hierarchy_id_cp0))
        self.fault_state_info_wallbox_socket = FaultState(ComponentInfo(None, "Wallbox-Steckdose", "wallbox_socket"))

        with SingleComponentUpdateContext(self.fault_state_info_cp0, reraise=True):
            self.init_gpio(mode)
        self.cp0_client_handler = None
        self.cp0_modbus_client = None
        self.cp0 = None
        self.wallbox_socket = None
        if mode != InternalChargepointMode.PRO_PLUS:
            with SingleComponentUpdateContext(self.fault_state_info_cp0):
                self.cp0_modbus_client, evse_ids = get_modbus_client(
                    mode, 0, fault_state=self.fault_state_info_cp0)
        if parent_wallbox_socket.data.detected and self.cp0_modbus_client is not None:
            with SingleComponentUpdateContext(self.fault_state_info_wallbox_socket):
                self.wallbox_socket = HandlerWallboxSocket(
                    self.cp0_modbus_client, global_data, parent_wallbox_socket)
        if self.cp0_modbus_client is not None or mode == InternalChargepointMode.PRO_PLUS:
            with SingleComponentUpdateContext(self.fault_state_info_cp0):
                if self.cp0_modbus_client is not None:
                    self.cp0_client_handler = ClientHandler(
                        0, self.cp0_modbus_client, evse_ids, self.fault_state_info_cp0)
                self.cp0 = HandlerChargepoint(self.cp0_client_handler, 0, mode,
                                              global_data, parent_cp0, hierarchy_id_cp0)
        try:
            if ((mode == InternalChargepointMode.DUO or mode == InternalChargepointMode.SE) and
                    hierarchy_id_cp1 is not None):
                fault_state_info_cp1 = FaultState(
                    ComponentInfo(1, "Interner Ladepunkt 1", "internal_chargepoint", hierarchy_id=hierarchy_id_cp1))
                with SingleComponentUpdateContext(fault_state_info_cp1, reraise=True):
                    log.debug("Zweiter Ladepunkt für Duo konfiguriert.")
                    self.cp1_client_handler = client_factory(mode, 1, fault_state_info_cp1, self.cp0_modbus_client)
                    self.cp1 = HandlerChargepoint(self.cp1_client_handler, 1, mode,
                                                  global_data, parent_cp1, hierarchy_id_cp1)
            else:
                self.cp1 = None
                self.cp1_client_handler = None
        except Exception:
            self.cp1 = None
            self.cp1_client_handler = None

    def init_gpio(self, mode: InternalChargepointMode) -> None:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(37, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(22, GPIO.OUT)
        GPIO.setup(29, GPIO.OUT)
        GPIO.setup(11, GPIO.OUT)
        GPIO.setup(15, GPIO.OUT)

        if mode in (InternalChargepointMode.SERIES, InternalChargepointMode.SE):
            GPIO.setup(26, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(23, GPIO.OUT, initial=GPIO.LOW)
        else:
            # GPIOs for socket
            GPIO.setup(23, GPIO.OUT)
            GPIO.setup(26, GPIO.OUT)
        GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def loop(self) -> None:
        def _loop():
            while True:
                if self.event_stop.is_set():
                    break
                clear_in_memory_log_handler("internal_chargepoint")
                log.debug("***Start***")
                data = copy.deepcopy(SubData.internal_chargepoint_data)
                log.debug(data)
                log.setLevel(SubData.system_data["system"].data["debug_level"])
                heartbeat_cp0, heartbeat_cp1 = self.cp0 is not None, True
                if self.cp0:
                    heartbeat_cp0 = self.cp0.update(data["global_data"], data["cp0"].data, data["rfid_data"])
                if self.cp1:
                    heartbeat_cp1 = self.cp1.update(data["global_data"], data["cp1"].data, data["rfid_data"])
                if self.wallbox_socket:
                    wallbox_socket_data = copy.deepcopy(SubData.wallbox_socket_data.data)
                    heartbeat_wallbox_socket = self.wallbox_socket.update(data["global_data"], wallbox_socket_data)
                self.heartbeat = True if heartbeat_cp0 and heartbeat_cp1 and (
                    self.wallbox_socket is None or heartbeat_wallbox_socket) else False
                time.sleep(1.1)
        # Allgemeine Fehlermeldungen an LP 1
        with SingleComponentUpdateContext(self.fault_state_info_cp0, update_always=False):
            clients = []
            is_pro_plus = self.cp0 is not None and self.cp0.mode == InternalChargepointMode.PRO_PLUS
            if not is_pro_plus:
                if self.cp0_modbus_client is not None:
                    clients.append(self.cp0_modbus_client)
                for handler in (self.cp0_client_handler, self.cp1_client_handler):
                    if handler is not None and handler.client not in clients:
                        clients.append(handler.client)
                if not clients:
                    log.error("Kein Modbus-Client vorhanden. Beende.")
                    return

            with ExitStack() as stack:
                for client in clients:
                    stack.enter_context(client)
                _loop()


class HandlerChargepoint:
    def __init__(self,
                 client_handler: Optional[ClientHandler],
                 local_charge_point_num: int,
                 mode: InternalChargepointMode,
                 global_data: GlobalHandlerData,
                 internal_cp: InternalChargepoint,
                 hierarchy_id: int) -> None:
        self.local_charge_point_num = local_charge_point_num
        self.mode = mode
        if local_charge_point_num == 0:
            if mode == InternalChargepointMode.SOCKET:
                self.module = Socket(local_charge_point_num, client_handler, internal_cp, hierarchy_id)
            elif mode == InternalChargepointMode.PRO_PLUS:
                self.module = ProPlus(local_charge_point_num, internal_cp, hierarchy_id)
            else:
                self.module = chargepoint_module.ChargepointModule(
                    local_charge_point_num, client_handler, internal_cp, hierarchy_id)
        else:
            self.module = chargepoint_module.ChargepointModule(
                local_charge_point_num, client_handler, internal_cp, hierarchy_id)
        with SingleComponentUpdateContext(self.module.fault_state):
            self.update_state = UpdateState(self.module, hierarchy_id)
            self.old_plug_state = False
            if global_data.parent_ip != "localhost":
                Pub().pub(f"openWB/set/chargepoint/{hierarchy_id}/get/state_str",
                          payload="Statusmeldungen bitte auf der Primary-openWB einsehen.")

    def update(self, global_data: GlobalHandlerData, data: InternalChargepointData, rfid_data: RfidData) -> bool:
        def __thread_active(thread: Optional[Thread]) -> bool:
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


class HandlerWallboxSocket:
    def __init__(self,
                 client: ModbusSerialClient_,
                 global_data: GlobalHandlerData,
                 wallbox_socket: WallboxSocket) -> None:
        self.module = WallboxSocketModule(client, wallbox_socket)
        self.global_data = global_data
        with SingleComponentUpdateContext(self.module.fault_state):
            self.update_state = UpdateWallboxSocketState(self.module)

    def update(self, global_data: GlobalHandlerData, data: WallboxSocketData) -> bool:
        with SingleComponentUpdateContext(self.module.fault_state):
            self.module.get_values(data.last_tag)
            heartbeat_expired = self._check_heartbeat_expired(global_data.heartbeat)
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
        self.event_stop = Event()
        self.event_start = Event()

    def auto_detect_wallbox_socket(self):
        try:
            device, count = get_serial_modbus_devices()
            if count == 1 and device[0] in BUS_SOURCES:
                port = device[0]
                client = ModbusSerialClient_(port)
                fault_state = FaultState(ComponentInfo(None, "Wallbox-Steckdose", "wallbox_socket"))
                if ClientHandler.find_meter_client(WALLBOX_SOCKET_METERS, client, fault_state) is not None:
                    pub.pub_single("openWB/internal_socket/data/detected", True)
                    with ModifyLoglevelContext(log, logging.DEBUG):
                        log.debug("Wallbox-Steckdose verbaut.")
                    return
            with ModifyLoglevelContext(log, logging.DEBUG):
                log.debug("Es konnte keine Wallbox-Steckdose erkannt werden.")
        except Exception:
            log.exception("Fehler bei der automatischen Erkennung einer Wallbox-Steckdose")

    def handler(self):
        self.auto_detect_wallbox_socket()
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
                        mode = InternalChargepointMode(cp.chargepoint.chargepoint_module.config.configuration.mode)
                        if cp.chargepoint.chargepoint_module.config.configuration.duo_num == 0:
                            hierarchy_id_cp0 = cp.chargepoint.num
                        else:
                            hierarchy_id_cp1 = cp.chargepoint.num

                try:
                    self.internal_chargepoint_handler = InternalChargepointHandler(
                        mode,
                        data["global_data"],
                        data["cp0"],
                        hierarchy_id_cp0,
                        data["cp1"],
                        hierarchy_id_cp1,
                        copy.deepcopy(SubData.wallbox_socket_data),
                        self.event_start,
                        self.event_stop)
                    self.internal_chargepoint_handler.loop()
                except UnboundLocalError:
                    log.debug("Kein interner Ladepunkt konfiguriert.")
            except Exception:
                log.exception("Fehler im internen Ladepunkt")
