^^
            
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
                    calculate_charge_cost(cp)
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
