#!/usr/bin/env python3
"""Starten der benötigten Prozesse
"""
# flake8: noqa: E402
import logging
from helpermodules import logger
from helpermodules.utils import run_command, thread_handler
import threading
import sys
import functools

# als erstes logging initialisieren, damit auch ImportError geloggt werden
logger.setup_logging()
log = logging.getLogger()

from pathlib import Path
from random import randrange
import schedule
import time
from threading import Event, Thread, enumerate
import traceback
from control.chargelog.chargelog import calc_energy_costs, calculate_charged_energy_by_source

from control import data, prepare, process
from control.algorithm import algorithm
from helpermodules import command, setdata, subdata, timecheck, update_config
from helpermodules.changed_values_handler import ChangedValuesContext
from helpermodules.measurement_logging.update_yields import update_daily_yields, update_pv_monthly_yearly_yields
from helpermodules.measurement_logging.write_log import LogType, save_log
from helpermodules.modbusserver import start_modbus_server
from helpermodules.pub import Pub
from modules import configuration, loadvars, update_soc
from modules.internal_chargepoint_handler.internal_chargepoint_handler import GeneralInternalChargepointHandler
from modules.internal_chargepoint_handler.gpio import InternalGpioHandler
from modules.internal_chargepoint_handler.rfid import RfidReader
from modules.utils import wait_for_module_update_completed
from smarthome.smarthome import readmq, smarthome_handler


class HandlerAlgorithm:
    def __init__(self):
        self.interval_counter = 1
        self.current_day = None
        self.handler_locks = {}
        self.handler_timestamps = {}

    def __acquire_lock(self, handler_name, error_threshold=60):
        """Versucht, den Lock für den angegebenen Handler zu erwerben.
        Erstellt Lock und Timestamp-Eintrag bei Bedarf dynamisch.
        Gibt True zurück, wenn der Lock erfolgreich erworben wurde, sonst False.
        """
        if handler_name not in self.handler_locks:
            self.handler_locks[handler_name] = threading.Lock()
        if handler_name not in self.handler_timestamps:
            self.handler_timestamps[handler_name] = 0

        lock = self.handler_locks[handler_name]
        now = time.time()
        if lock.acquire(blocking=False):
            self.handler_timestamps[handler_name] = now
            log.debug(f"Lock für {handler_name} erworben.")
            return True
        # Wenn der Lock älter als 'error_threshold' Sekunden ist, wird ein Error geloggt.
        log_handler = log.error if now - self.handler_timestamps[handler_name] > error_threshold else log.debug
        log_handler(
            f"{handler_name} läuft bereits, neuer Aufruf wird übersprungen. Letzter Start: "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.handler_timestamps[handler_name]))} "
            f"(vor {now - self.handler_timestamps[handler_name]} Sekunden).")
        return False

    def __release_lock(self, handler_name):
        """Gibt den Lock für den angegebenen Handler frei."""
        lock = self.handler_locks.get(handler_name)
        if lock:
            lock.release()
            log.debug(f"Lock für {handler_name} freigegeben nach {time.time() - self.handler_timestamps[handler_name]} Sekunden.")
            self.handler_timestamps.pop(handler_name, None)
        else:
            log.warning(f"Lock für {handler_name} nicht gefunden.")

    def __with_handler_lock(error_threshold=60):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                handler_name = func.__name__
                if self.__acquire_lock(handler_name, error_threshold):
                    try:
                        return func(self, *args, **kwargs)
                    finally:
                        self.__release_lock(handler_name)
                else:
                    return
            return wrapper
        return decorator

    def monitor_handler_locks(self, max_runtime=300):
        emergency_exit = False
        for handler_name, lock in self.handler_locks.items():
            if lock.locked():
                # Überprüfen, wie lange der Lock bereits aktiv ist
                duration = time.time() - self.handler_timestamps[handler_name]
                log.warning(f"Handler {handler_name} ist seit {duration} Sekunden gesperrt.")
                # Stack Trace des Threads, der den Lock hält
                for tid, frame in sys._current_frames().items():
                    if tid == lock._get_ident():
                        stack_trace = traceback.format_stack(frame)
                        log.warning(f"Stack Trace für {handler_name}:")
                        for line in stack_trace:
                            log.warning(line.strip())
                if duration > max_runtime:
                    log.error(f"Handler {handler_name} ist seit mehr als {max_runtime} Sekunden gesperrt.")
                    emergency_exit = True
        if emergency_exit:
            log.error(f"Deadlock erkannt, Prozess wird beendet!")
            log.debug(f"Threads: {enumerate()}")
            for thread in enumerate():
                logging.debug(f"Thread Name: {thread.name}")
                if hasattr(thread, "ident"):
                    thread_id = thread.ident
                    for tid, frame in sys._current_frames().items():
                        if tid == thread_id:
                            logging.debug(f"  File: {frame.f_code.co_filename}, Line: {frame.f_lineno}, Function: {frame.f_code.co_name}")
                            stack_trace = traceback.format_stack(frame)
                            logging.debug("  Stack Trace:")
                            for line in stack_trace:
                                logging.debug(line.strip())
            sys.exit(1)

    # decorator can not be used here as it would block logging before handler_with_control_interval()
    # @__with_handler_lock(error_threshold=30)
    def handler10Sec(self):
        """ führt den Algorithmus durch.
        """
        try:
            def handler_with_control_interval():
                if (data.data.general_data.data.control_interval / 10) == self.interval_counter:
                    data.data.copy_data()
                    loadvars_.get_values()
                    wait_for_module_update_completed(loadvars_.event_module_update_completed,
                                                     "openWB/set/system/device/module_update_completed")
                    data.data.copy_data()
                    with ChangedValuesContext(loadvars_.event_module_update_completed):
                        self.heartbeat = True
                        if data.data.system_data["system"].data["perform_update"]:
                            data.data.system_data["system"].perform_update()
                            return
                        elif data.data.system_data["system"].data["update_in_progress"]:
                            log.info("Regelung pausiert, da ein Update durchgeführt wird.")
                        event_global_data_initialized.set()
                        prep.setup_algorithm()
                        control.calc_current()
                        proc.process_algorithm_results()
                        data.data.graph_data.pub_graph_data()
                    self.interval_counter = 1
                else:
                    self.interval_counter = self.interval_counter + 1
            
            # In-Memory Log-Handler zurücksetzen
            logger.clear_in_memory_log_handler("main")

            log.info("# ***Start*** ")
            # log.debug(run_command.run_shell_command("top -b -n 1 | head -n 20"))
            # log.debug(f'Drosselung: {run_command.run_shell_command("if which vcgencmd >/dev/null; then vcgencmd get_throttled; else echo not found; fi")}')
            Pub().pub("openWB/set/system/time", timecheck.create_timestamp())
            if not self.__acquire_lock("handler10Sec", error_threshold=30):
                return
            try:
                handler_with_control_interval()
                logger.write_logs_to_file("main")
            finally:
                self.__release_lock("handler10Sec")
        except Exception:
            log.exception("Fehler im Main-Modul")

    @__with_handler_lock(error_threshold=60)
    def handler5MinAlgorithm(self):
        """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben
        ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
        """
        try:
            with ChangedValuesContext(loadvars_.event_module_update_completed):
                totals = save_log(LogType.DAILY)
                update_daily_yields(totals)
                update_pv_monthly_yearly_yields()
                for cp in data.data.cp_data.values():
                    calc_energy_costs(cp)
                data.data.general_data.grid_protection()
                data.data.optional_data.ocpp_transfer_meter_values()
                data.data.counter_all_data.validate_hierarchy()
        except Exception:
            log.exception("Fehler im Main-Modul")

    @__with_handler_lock(error_threshold=60)
    def handler5Min(self):
        """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben
        ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
        """
        try:
            log.debug("5 Minuten Handler ausführen.")
            if not sub.heartbeat:
                log.error("Heartbeat für Subdata nicht zurückgesetzt.")
                sub.disconnect()
                thread_handler(Thread(target=sub.sub_topics, args=(), name="Subdata"))
            else:
                sub.heartbeat = False

            if not set.heartbeat:
                log.error("Heartbeat für Setdata nicht zurückgesetzt.")
                set.disconnect()
                thread_handler(Thread(target=set.set_data, args=(), name="Setdata"))
            else:
                set.heartbeat = False

            if sub.internal_chargepoint_data["global_data"].configured:
                if not general_internal_chargepoint_handler.internal_chargepoint_handler.heartbeat:
                    log.error("Heartbeat für Internen Ladepunkt nicht zurückgesetzt.")
                    general_internal_chargepoint_handler.event_stop.set()
                    general_internal_chargepoint_handler.event_start.set()
                else:
                    general_internal_chargepoint_handler.internal_chargepoint_handler.heartbeat = False
            with ChangedValuesContext(loadvars_.event_module_update_completed):
                sub.system_data["system"].update_ip_address()
            
            # In-Memory Log-Handler zurücksetzen
            logger.clear_in_memory_log_handler("main")

            log.info("# ***Start*** ")
            # log.debug(run_command.run_shell_command("top -b -n 1 | head -n 20"))
            # log.debug(f'Drosselung: {run_command.run_shell_command("if which vcgencmd >/dev/null; then vcgencmd get_throttled; else echo not found; fi")}')
            Pub().pub("openWB/set/system/time", timecheck.create_timestamp())
            if not self.__acquire_lock("handler10Sec", error_threshold=30):
                return
            try:
                logger.write_logs_to_file("main")
            finally:
                self.__release_lock("handler10Sec")
        except Exception:
            log.exception("Fehler im Main-Modul")

    @__with_handler_lock(error_threshold=60)
    def handler5MinAlgorithm(self):
        """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben
        ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
        """
        try:
            with ChangedValuesContext(loadvars_.event_module_update_completed):
                totals = save_log(LogType.DAILY)
                update_daily_yields(totals)
                update_pv_monthly_yearly_yields()
                data.data.general_data.grid_protection()
                data.data.optional_data.ocpp_transfer_meter_values()
                data.data.counter_all_data.validate_hierarchy()
        except Exception:
            log.exception("Fehler im Main-Modul")

    @__with_handler_lock(error_threshold=60)
    def handler5Min(self):
        """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben
        ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
        """
        try:
            log.debug("5 Minuten Handler ausführen.")
            if not sub.heartbeat:
                log.error("Heartbeat für Subdata nicht zurückgesetzt.")
                sub.disconnect()
                thread_handler(Thread(target=sub.sub_topics, args=(), name="Subdata"))
            else:
                sub.heartbeat = False

            if not set.heartbeat:
                log.error("Heartbeat für Setdata nicht zurückgesetzt.")
                set.disconnect()
                thread_handler(Thread(target=set.set_data, args=(), name="Setdata"))
            else:
                set.heartbeat = False

            if sub.internal_chargepoint_data["global_data"].configured:
                if not general_internal_chargepoint_handler.internal_chargepoint_handler.heartbeat:
                    log.error("Heartbeat für Internen Ladepunkt nicht zurückgesetzt.")
                    general_internal_chargepoint_handler.event_stop.set()
                    general_internal_chargepoint_handler.event_start.set()
                else:
                    general_internal_chargepoint_handler.internal_chargepoint_handler.heartbeat = False
            with ChangedValuesContext(loadvars_.event_module_update_completed):
                sub.system_data["system"].update_ip_address()
            data.data.optional_data.et_get_prices()
        except Exception:
            log.exception("Fehler im Main-Modul")

    @__with_handler_lock(error_threshold=60)
    def handler_midnight(self):
        try:
            save_log(LogType.MONTHLY)
            thread_errors_path = Path(Path(__file__).resolve().parents[1]/"ramdisk"/"thread_errors.log")
            with thread_errors_path.open("w") as f:
                f.write("")
        except Exception:
            log.exception("Fehler im Main-Modul")

    @__with_handler_lock(error_threshold=60)
    def handler_random_nightly(self):
        log.warning("Display wird neu geladen.")  # nur zur Info im Log
        # chromium neu starten, um größere Auswirkungen eines Speicherlecks zu vermeiden
        run_command.run_command([
            str(Path(__file__).resolve().parents[1] / "runs" / "update_local_display.sh"), "1"
        ], process_exception=True)
        try:
            data.data.system_data["system"].thread_backup_and_send_to_cloud()
        except Exception:
            log.exception("Fehler im Main-Modul")

    @__with_handler_lock(error_threshold=60)
    def handler_hour(self):
        """ Handler, der jede Stunde aufgerufen wird und die Aufgaben ausführt, die nur jede Stunde ausgeführt werden müssen.
        """
        try:
            with ChangedValuesContext(loadvars_.event_module_update_completed):
                for cp in data.data.cp_data.values():
                    calculate_charged_energy_by_source(cp)
            logger.clear_in_memory_log_handler(None)
        except Exception:
            log.exception("Fehler im Main-Modul")


def schedule_jobs():
    [schedule.every().minute.at(f":{i:02d}").do(smarthome_handler).tag("algorithm") for i in range(0, 60, 5)]
    [schedule.every().hour.at(f":{i:02d}").do(handler.handler5Min) for i in range(0, 60, 5)]
    [schedule.every().hour.at(f":{i:02d}").do(handler.handler5MinAlgorithm).tag("algorithm") for i in range(0, 60, 5)]
    [schedule.every().day.at(f"{i:02d}:00").do(handler.handler_hour).tag("algorithm") for i in range(0, 24, 1)]
    # every().hour ruft nicht jede Stunde den Handler auf.
    # schedule.every().hour.do(handler.handler_hour).tag("algorithm")
    schedule.every().day.at("00:00:00").do(handler.handler_midnight).tag("algorithm")
    schedule.every().day.at(f"0{randrange(0, 5)}:{randrange(0, 59):02d}:{randrange(0, 59):02d}").do(
        handler.handler_random_nightly)
    [schedule.every().minute.at(f":{i:02d}").do(handler.handler10Sec).tag("algorithm") for i in range(0, 60, 10)]
    # 30 Sekunden Handler, der die Locks überwacht, Deadlocks erkennt, loggt und ggf. den Prozess beendet
    schedule.every(30).seconds.do(handler.monitor_handler_locks, max_runtime=600)


try:
    log.debug("Start openWB2.service")
    old_memory_usage = 0
    loadvars_ = loadvars.Loadvars()
    data.data_init(loadvars_.event_module_update_completed)
    update_config.UpdateConfig().update()
    configuration.pub_configurable()

    # run as thread for logging reasons
    t_smarthome = Thread(target=readmq, args=(), name="smarthome")
    t_smarthome.start()
    t_smarthome.join()

    proc = process.Process()
    control = algorithm.Algorithm()
    handler = HandlerAlgorithm()
    prep = prepare.Prepare()
    general_internal_chargepoint_handler = GeneralInternalChargepointHandler()
    rfid = RfidReader()
    event_ev_template = Event()
    event_ev_template.set()
    event_cp_config = Event()
    event_cp_config.set()
    event_soc = Event()
    event_soc.set()
    event_copy_data = Event()  # set: Kopieren abgeschlossen, reset: es wird kopiert
    event_copy_data.set()
    event_global_data_initialized = Event()
    event_command_completed = Event()
    event_command_completed.set()
    event_subdata_initialized = Event()
    event_update_config_completed = Event()
    event_modbus_server = Event()
    event_jobs_running = Event()
    event_jobs_running.set()
    event_update_soc = Event()
    event_restart_gpio = Event()
    gpio = InternalGpioHandler(event_restart_gpio)
    prep = prepare.Prepare()
    soc = update_soc.UpdateSoc(event_update_soc)
    set = setdata.SetData(event_ev_template,
                          event_cp_config, event_soc,
                          event_subdata_initialized)
    sub = subdata.SubData(event_ev_template,
                          event_cp_config, loadvars_.event_module_update_completed,
                          event_copy_data, event_global_data_initialized, event_command_completed,
                          event_subdata_initialized, soc.event_vehicle_update_completed,
                          general_internal_chargepoint_handler.event_start,
                          general_internal_chargepoint_handler.event_stop,
                          event_update_config_completed,
                          event_update_soc,
                          event_soc,
                          event_jobs_running, event_modbus_server, event_restart_gpio)
    comm = command.Command(event_command_completed)
    t_sub = Thread(target=sub.sub_topics, args=(), name="Subdata")
    t_set = Thread(target=set.set_data, args=(), name="Setdata")
    t_comm = Thread(target=comm.sub_commands, args=(), name="Commands")
    t_soc = Thread(target=soc.update, args=(), name="SoC")
    t_internal_chargepoint = Thread(target=general_internal_chargepoint_handler.handler,
                                    args=(), name="Internal Chargepoint")
    if rfid.keyboards_detected:
        t_rfid = Thread(target=rfid.run, args=(), name="Internal RFID")
        t_rfid.start()

    t_gpio = Thread(target=gpio.loop, args=(), name="Internal GPIO")
    t_gpio.start()

    t_sub.start()
    t_set.start()
    t_comm.start()
    t_soc.start()
    t_internal_chargepoint.start()
    Thread(target=start_modbus_server, args=(event_modbus_server,), name="Modbus Control Server").start()
    # Warten, damit subdata Zeit hat, alle Topics auf dem Broker zu empfangen.
    event_update_config_completed.wait(300)
    event_subdata_initialized.wait(300)
    Pub().pub("openWB/set/system/boot_done", True)
    Path(Path(__file__).resolve().parents[1]/"ramdisk"/"bootdone").touch()
    schedule_jobs()
    if event_jobs_running.is_set():
        # Nach dem Starten als erstes den 10Sek-Handler aufrufen, damit die Werte der data.data initialisiert werden.
        handler.handler10Sec()
except Exception:
    log.exception("Fehler im Main-Modul")

while True:
    try:
        if event_jobs_running.is_set() and len(schedule.get_jobs("algorithm")) == 0:
            schedule_jobs()
        elif event_jobs_running.is_set() is False and len(schedule.get_jobs("algorithm")) > 0:
            schedule.clear("algorithm")
        schedule.run_pending()
        time.sleep(1)
    except Exception:
        log.exception("Fehler im Main-Modul")
