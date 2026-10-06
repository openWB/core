import asyncio
import logging
import math
from dataclasses import asdict
from pathlib import Path
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from ocpp.v16 import ChargePoint as cp
    from ocpp.v16 import call, call_result, datatypes
    from ocpp.v16.enums import (
        Action,
        AvailabilityStatus,
        AvailabilityType,
        ChargePointErrorCode,
        ChargePointStatus,
        ConfigurationStatus,
        RemoteStartStopStatus,
        UnlockStatus,
        ResetStatus,
        ResetType,
        DiagnosticsStatus,
        MessageTrigger,
        TriggerMessageStatus,
        ClearCacheStatus,
    )
    from ocpp.routing import after, on
from typing import Optional
from helpermodules.pub import Pub


from control import data
from modules.common.fault_state import FaultState
from control.ocpp.helper import _get_formatted_time, get_cp_from_chargebox_id
from control.ocpp.helper_diagnostics import create_diagnostics, upload_diagnostics

log = logging.getLogger(__name__)


class OcppChargePoint(cp):

    def __init__(self, chargebox_id, ws, reset_callback=None, trigger_msg_callback=None):
        super().__init__(chargebox_id, ws)
        self.chargebox_id = chargebox_id
        self.ws = ws

        self.reset_callback = reset_callback
        self.trigger_msg_callback = trigger_msg_callback
        self._accepted_triggers = set()
        self._diagnostics_status_stored = None
        self.registration_state = None

    async def _handle_call(self, msg):
        state = getattr(self.registration_state, "value", self.registration_state)
        if state == "Rejected":
            log.info(
                "OCPP Call %s von der Zentrale während Rejected ignoriert",
                msg.action,
            )
            return
        return await super()._handle_call(msg)

    # Der openWB-Chargepoint kann beim Reconnect neu erzeugt werden.
    @property
    def openwb_cp(self):
        return get_cp_from_chargebox_id(self.chargebox_id)

    @property
    def openwb_num(self):
        openwb_cp = self.openwb_cp
        return openwb_cp.num if openwb_cp is not None else None

    async def _start_transaction(self,
                                 connector_id: int,
                                 id_tag: str,
                                 imported: int) -> Optional[object]:

        print(f"# START_TRANSACTION        CP {self.openwb_num} OCPP_Nr: {self.chargebox_id}")
        log.debug(f"Start Transaktion für CP {self.openwb_num} mit OCPP_Nr: {self.chargebox_id}")
        request = call.StartTransaction(
            connector_id=connector_id,
            id_tag=id_tag if id_tag else "",
            meter_start=int(imported),
            timestamp=_get_formatted_time(),
        )

        response: call_result.StartTransaction = await self.call(request)
        print(f"# StartTransaction response: {response}")
        log.debug(f"StartTransaction response: {response}")

        return response

    async def _boot_notification(self):
        try:
            print(f"# BOOT_NOTIFICATION        CP {self.openwb_num} OCPP_Nr: {self.chargebox_id}")
            log.debug(f"Boot Notification für CP {self.openwb_num} mit OCPP_Nr: {self.chargebox_id}")
            request = call.BootNotification(
                charge_point_model=self.openwb_cp.chargepoint_module.config.type,
                charge_point_vendor="openWB",
                firmware_version=data.data.system_data["system"].data["version"],
                meter_serial_number=self.openwb_cp.data.get.serial_number
            )
            response: call_result.BootNotification = await self.call(request)
            print(f"# BootNotification response: {response}")
            log.debug(f"BootNotification response: {response}")
            return response

        except Exception as e:
            print(f"# Exception occurred: {e}")
            log.exception(
                f"Exception occurred during Boot Notification for CP Nr: {self.openwb_num} "
                f"OCPP_Nr: {self.chargebox_id}: {e}")
        return None

    async def _authorize(self,
                         id_tag: str) -> Optional[object]:

        print(f"AUTHORIZE        CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")

        request = call.Authorize(
            id_tag=id_tag if id_tag else ""
        )

        response: call_result.Authorize = await self.call(request)
        print(f"Authorize response: {response}")

        return response

    async def _stop_transaction(self,
                                reason: str,
                                transaction_id: int,
                                id_tag: str,
                                meter_stop: int) -> Optional[object]:

        print(f"# STOP_TRANSACTION        CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")
        log.debug(f"Stop Transaction for CP {self.openwb_num} OCPP_Nr: {self.chargebox_id}")
        request = call.StopTransaction(
            meter_stop=int(meter_stop),
            transaction_id=transaction_id,
            reason=reason,
            id_tag=id_tag if id_tag else "",
            timestamp=_get_formatted_time(),
        )
        response: call_result.StopTransaction = await self.call(request)
        print(f"# StopTransaction response: {response}")
        log.debug(f"StopTransaction response: {response}")
        return response

    async def _heartbeat(self) -> Optional[object]:
        print(f"# HEART_BEAT              CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")
        log.debug(f"Heartbeat for CP {self.openwb_num} OCPP_Nr: {self.chargebox_id}")
        request = call.Heartbeat()
        response: call_result.Heartbeat = await self.call(request)
        print(f"# Heartbeat response: {response}")
        log.debug(f"Heartbeat response: {response}")
        return response

    async def _meter_values(self,
                            connector_id: int,
                            transaction_id: int,
                            meter_value: list) -> Optional[object]:
        print(f"# METER_VALUES            CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")
        log.debug(
            f"Send MeterValues for CP {self.openwb_num} OCPP_Nr: {self.chargebox_id} "
            f"transaction_id: {transaction_id}, meter_value: {meter_value}")
        request = call.MeterValues(
            connector_id=connector_id,
            transaction_id=transaction_id,
            meter_value=meter_value
        )
        response: call_result.MeterValues = await self.call(request)
        print(f"# MeterValues response: {response}")
        log.debug(f"MeterValues response: {response}")
        return response

    async def _status_notification(self,
                                   connector_id: int,
                                   fault_state: FaultState,
                                   fault_state_str: str,
                                   status: ChargePointStatus,
                                   force: bool = False) -> Optional[object]:

        print(f"# STATUS_NOTIFICATION     CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")
        print(f"# --------- Status notification requested for connector: {connector_id}")
        log.debug(f"Status change detected for CP {self.openwb_num} mit OCPP_Nr: {self.chargebox_id} "
                  f"New Status: {(status, get_ocpp_error_code(fault_state))} "
                  f"for connector: {connector_id}")

        # Key rausschicken
        request = call.StatusNotification(
            connector_id=connector_id,
            error_code=get_ocpp_error_code(fault_state),
            status=status,
            timestamp=_get_formatted_time(),
            info=fault_state_str,
            vendor_id="openWB",
            vendor_error_code=str(fault_state)

        )
        response: call_result.StatusNotification = await self.call(request)
        print(f"# StatusNotification response: {response}")
        log.debug(f"StatusNotification response: {response}")

        return response

    @on(Action.change_availability)
    async def on_change_availability(
            self,
            connector_id: int,
            type: AvailabilityType,
            **kwargs,
    ):
        try:
            availability_type = type
            print(
                f"CHANGE_AVAILABILITY     CP_Nr: {self.openwb_num} "
                f"OCPP_Nr: {self.chargebox_id}"
            )

            if connector_id not in (0, 1):
                log.warning("Ungültige Connector-ID für ChangeAvailability: %s", connector_id)
                return call_result.ChangeAvailability(
                    status=AvailabilityStatus.rejected
                )

            if (availability_type == AvailabilityType.inoperative
                    and self.openwb_cp.data.get.ocpp.transaction_id is not None):
                self.openwb_cp.data.get.ocpp.pending_availability = True
                Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/get/ocpp/pending_availability", True)
                return call_result.ChangeAvailability(
                    status=AvailabilityStatus.scheduled
                )

            await self._set_availability(availability_type)

            self.openwb_cp.data.get.ocpp.pending_availability = False
            Pub().pub(
                f"openWB/set/chargepoint/{self.openwb_num}/get/ocpp/pending_availability",
                False,
            )

            return call_result.ChangeAvailability(
                status=AvailabilityStatus.accepted
            )

        except Exception:
            log.exception("Fehler bei ChangeAvailability für %s", self.chargebox_id)
            return call_result.ChangeAvailability(
                status=AvailabilityStatus.rejected
            )

    async def _set_availability(self, availability_type: AvailabilityType):
        openwb_cp = self.openwb_cp
        if openwb_cp is None:
            return
        available = availability_type == AvailabilityType.operative
        openwb_cp.data.get.ocpp.availability = available

        Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/get/ocpp/availability",
                  available)

    async def apply_pending_availability(self):
        openwb_cp = self.openwb_cp
        if openwb_cp is None or not openwb_cp.data.get.ocpp.pending_availability:
            return

        await self._set_availability(AvailabilityType.inoperative)
        openwb_cp.data.get.ocpp.pending_availability = False
        Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/get/ocpp/pending_availability", False)

    @on(Action.get_configuration)
    async def get_configuration(self, key=None, **kwargs):
        print(
            f"GET_CONFIGURATION     CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nKey: {key}"
        )

        unknown_keys = []
        configuration = self.openwb_cp.data.get.ocpp.config
        configuration_fields = vars(configuration)
        requested_keys = ([key] if isinstance(key, str) else key) or []

        if requested_keys:
            configuration_values = []
            for requested_key in requested_keys:
                if requested_key not in configuration_fields:
                    unknown_keys.append(requested_key)
                    continue
                configuration_values.append(
                    (requested_key, configuration_fields[requested_key])
                )
        else:
            configuration_values = configuration_fields.items()

        response = dict(
            configuration_key=[
                datatypes.KeyValue(
                    key=k,
                    readonly=False,
                    value=str(v)
                ) for k, v in configuration_values
            ],
            unknown_key=unknown_keys
        )
        print(response)
        return call_result.GetConfiguration(
            configuration_key=response["configuration_key"],
            unknown_key=response["unknown_key"]
        )

    @on(Action.change_configuration)
    async def change_configuration(self, key, value, **kwargs):
        print(
            f"CHANGE_CONFIGURATION  CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nKey: {key} "
            f"Value: {value}"
        )

        configuration = self.openwb_cp.data.get.ocpp.config
        configuration_fields = vars(configuration)
        if key not in configuration_fields:
            return call_result.ChangeConfiguration(
                status=ConfigurationStatus.not_supported
            )

        current_value = configuration_fields[key]
        try:
            if isinstance(current_value, bool):
                normalized_value = value.strip().lower()
                if normalized_value not in ("true", "false"):
                    raise ValueError("Boolean-Konfigurationswert muss true oder false sein")
                parsed_value = normalized_value == "true"
            elif isinstance(current_value, int):
                parsed_value = int(value)
            elif isinstance(current_value, float):
                parsed_value = float(value)
                if not math.isfinite(parsed_value):
                    raise ValueError("Float-Konfigurationswert muss endlich sein")
            elif isinstance(current_value, str):
                parsed_value = value
            else:
                return call_result.ChangeConfiguration(
                    status=ConfigurationStatus.rejected
                )
        except (AttributeError, TypeError, ValueError, OverflowError):
            return call_result.ChangeConfiguration(
                status=ConfigurationStatus.rejected
            )

        # diese Parameter unterstützen nur nur Werte größer 0
        if key in ("HeartbeatInterval", "MeterValueSampleInterval"):
            if parsed_value <= 0:
                return call_result.ChangeConfiguration(
                    status=ConfigurationStatus.rejected
                )

        # Update Data und Broker
        await self.set_configuration_value(key, parsed_value)

        return call_result.ChangeConfiguration(
            status=ConfigurationStatus.accepted
        )

    @on(Action.remote_start_transaction)
    async def remote_start_transaction(self, id_tag: str, connector_id: Optional[int] = None, **kwargs):
        if getattr(self.registration_state, "value", self.registration_state) == "Pending":
            return call_result.RemoteStartTransaction(
                status=RemoteStartStopStatus.rejected
            )

        print(
            f"REMOTE_START_TRANSACTION  CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nId Tag: {id_tag} "
            f"Connector ID: {connector_id} "
            f"\nKwargs: {kwargs}"
        )

        """
        Wenn der Cp nicht gesperrt ist durch OCPP_Availability,
        kann die Remote-Start-Transaktion akzeptiert werden.

        Wir setzten einfach den übergebenen id_tag  in die rfif-Topic
        dann handelt alles weiter der openWB-Backend

        Wenn Tag erlaubt ist:
        wenn Fahrzeug nicht eingesteckt ist -> Nachricht: sie haben 5 min um das auto einzustecken.
        wenn Fahrzeug eingesteckt ist -> Transaktion wird gestartet.
            -> standart reaction von openWB, wie wenn man direkt nen tag gescannt hat

        """
        requested_connector_id = connector_id if connector_id is not None else 1
        openwb_cp = self.openwb_cp
        if (openwb_cp is None or requested_connector_id != 1 or
                not openwb_cp.data.get.ocpp.availability):
            return call_result.RemoteStartTransaction(
                status=RemoteStartStopStatus.rejected
            )

        if openwb_cp.data.get.ocpp.transaction_id is not None:
            return call_result.RemoteStartTransaction(
                status=RemoteStartStopStatus.rejected
            )

        # Ich sag einfach hier ist das RFID-Tag
        # Wenn der CP das akzeptiert, wird die Transaktion gestartet
        Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/get/rfid", id_tag)

        return call_result.RemoteStartTransaction(
            status=RemoteStartStopStatus.accepted
        )

    @on(Action.remote_stop_transaction)
    async def remote_stop_transaction(self, transaction_id: int, **kwargs):
        if getattr(self.registration_state, "value", self.registration_state) == "Pending":
            return call_result.RemoteStopTransaction(
                status=RemoteStartStopStatus.rejected
            )

        print(
            f"REMOTE_STOP_TRANSACTION  CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nTransaction ID: {transaction_id} "
            f"\nKwargs: {kwargs}"
        )

        # Nur akzeptiren, wenn auch eine aktive Transaktion vorhanden ist
        # und die transaction_id übereinstimmt
        if (self.openwb_cp is not None and self.openwb_cp.data.get.ocpp.transaction_id is not None and
                self.openwb_cp.data.get.ocpp.transaction_id == transaction_id):
            self.openwb_cp.data.get.ocpp.remote_stop = True
            Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/get/ocpp/remote_stop", True)
        else:
            return call_result.RemoteStopTransaction(
                status=RemoteStartStopStatus.rejected
            )

        return call_result.RemoteStopTransaction(
            status=RemoteStartStopStatus.accepted
        )

    @on(Action.unlock_connector)
    async def unlock_connector(self, connector_id: int, **kwargs):
        # Nur wenn der Stecker nicht fest mit der Wallbox verbunden ist relevant
        # Also nur wenn beim kabel an beiden Seiten ein Stecker ist
        #
        # Antwort mit not_supported muss trotzdem gesendet werden!
        return call_result.UnlockConnector(
            status=UnlockStatus.not_supported
        )

    @on(Action.clear_cache)
    async def clear_cache(self, **kwargs):
        # Wir führen aktuell keine Authorization Cache
        # An den Server muss aber trotzdem eine Antwort gesendet werden!
        return call_result.ClearCache(
            status=ClearCacheStatus.rejected
        )

    @on(Action.reset)
    async def reset(self, type: ResetType, **kwargs):
        print(
            f"RESET  CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nType: {type} "
            f"\nKwargs: {kwargs}"
        )

        if self.reset_callback is None:
            log.error(
                "Kein Reset-Callback für OCPP Chargebox %s registriert",
                self.chargebox_id,
            )
            return call_result.Reset(status=ResetStatus.rejected)

        loop = asyncio.get_running_loop()

        # Die Reset-Antwort erst über die bestehende OCPP-Verbindung senden,
        # bevor der Callback beim Soft-Reset den Reconnect startet.
        loop.call_later(
            0.5,
            lambda: asyncio.create_task(
                self.reset_callback(
                    self.chargebox_id,
                    ResetType(type),
                )
            )
        )

        return call_result.Reset(
            status=ResetStatus.accepted
        )

    @on(Action.get_diagnostics)
    async def get_diagnostics(self,
                              location: str,
                              retries: Optional[int] = None,
                              retry_interval: Optional[int] = None,
                              start_time: Optional[str] = None,
                              stop_time: Optional[str] = None,
                              **kwargs):
        print(
            f"GET_DIAGNOSTICS  CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nKwargs: {kwargs}"
        )
        log.debug("#############################. TEST")
        filename = await create_diagnostics(start_time, stop_time)

        # Upload in einem eigenen Task
        asyncio.create_task(self._upload_diagnostics(filename, location, retries or 0, retry_interval or 0))

        # Nur den Namen der Datei zurückgeben, nicht den gesamten Pfad
        return call_result.GetDiagnostics(
            file_name=Path(filename).name
        )

    async def _upload_diagnostics(self,
                                  filepath,
                                  location,
                                  retries: Optional[int] = None,
                                  retry_interval: Optional[int] = None):
        log.debug(
            "Uploading diagnostics file: %s to location: %s with retries: %s and retry_interval: %s",
            filepath,
            location,
            retries,
            retry_interval
        )

        try:
            # Set status to uploading
            await self._diagnostics_status(DiagnosticsStatus.uploading)

            await upload_diagnostics(filepath, location, retries or 0, retry_interval or 0)

            await self._diagnostics_status(DiagnosticsStatus.uploaded)
        except Exception as e:
            log.exception("Fehler beim Hochladen der Diagnosedatei: %s", e)
            await self._diagnostics_status(DiagnosticsStatus.upload_failed)
        finally:
            # Status wieder auf 'idle' setzen
            # damit bei späteren Upload-Versuchen kein veralteter Status verwendet wird
            await self._diagnostics_status(DiagnosticsStatus.idle)
            # Temp-file wieder löschen
            # egal ob das Hochladen erfolgreich war oder nicht
            Path(filepath).unlink(missing_ok=True)

    async def _diagnostics_status(self, status: DiagnosticsStatus = None):

        if status is None:
            # sende den gespeicherten Diagnosestatus an die Zentrale
            if self._diagnostics_status_stored is None:
                # Wenn kein gespeicherter Status vorhanden ist, setze den Status auf 'idle'
                status = DiagnosticsStatus.idle
            else:
                # Wenn kein Status übergeben wurde, verwende den gespeicherten Status
                status = self._diagnostics_status_stored

        else:
            # speichere den neuen Status
            self._diagnostics_status_stored = status

        print(f"Setting diagnostics status: {status}")
        request = call.DiagnosticsStatusNotification(
            status=status
        )
        response = await self.call(request)
        return response

    @on(Action.trigger_message)
    async def trigger_message(self, requested_message: MessageTrigger,
                              connector_id: Optional[int] = None,
                              call_unique_id: Optional[str] = None, **kwargs):
        log.debug(
            "TRIGGER_MESSAGE CP_Nr: %s OCPP_Nr: %s Requested Message: %s Connector: %s",
            self.openwb_num,
            self.chargebox_id,
            requested_message,
            connector_id,
        )

        if requested_message not in (MessageTrigger.boot_notification,
                                     MessageTrigger.heartbeat,
                                     MessageTrigger.meter_values,
                                     MessageTrigger.status_notification,
                                     MessageTrigger.diagnostics_status_notification):
            return call_result.TriggerMessage(status=TriggerMessageStatus.not_implemented)

        if (self.trigger_msg_callback is None or self.openwb_cp is None or
                (requested_message == MessageTrigger.status_notification and connector_id not in (None, 0, 1))):
            return call_result.TriggerMessage(status=TriggerMessageStatus.rejected)

        if call_unique_id is not None:
            self._accepted_triggers.add(call_unique_id)
        return call_result.TriggerMessage(status=TriggerMessageStatus.accepted)

    @after(Action.trigger_message)
    async def after_trigger_message(self, requested_message: MessageTrigger,
                                    connector_id: Optional[int] = None,
                                    call_unique_id: Optional[str] = None, **kwargs):
        if call_unique_id not in self._accepted_triggers:
            return
        self._accepted_triggers.remove(call_unique_id)
        try:
            await self.trigger_msg_callback(self, requested_message, connector_id)
        except Exception:
            log.exception("TriggerMessage-Versand für %s fehlgeschlagen", self.chargebox_id)

    async def set_configuration_value(self, key: str, value):
        configuration = self.openwb_cp.data.get.ocpp.config
        setattr(configuration, key, value)
        Pub().pub(
            f"openWB/set/chargepoint/{self.openwb_num}/get/ocpp/config",
            asdict(configuration),
        )


def get_ocpp_error_code(fault_state: FaultState):
    if fault_state:
        return ChargePointErrorCode.other_error
    return ChargePointErrorCode.no_error
