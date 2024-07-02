#!/usr/bin/env python3
import logging
import time
import grpc
import modules.vehicles.evcc.vehicle_pb2 as vehicle_pb2
import modules.vehicles.evcc.vehicle_pb2_grpc as vehicle_pb2_grpc

from modules.common.abstract_vehicle import VehicleUpdateData
from modules.vehicles.evcc.config import EVCCVehicleSocConfiguration, EVCCVehicleSoc
from modules.common.component_state import CarState
from typing import Mapping, cast
from dataclass_utils import asdict
from helpermodules.pub import Pub

log = logging.getLogger(__name__)
evcc_endpoint = 'sponsor.evcc.io:8080'
gRPCRetryTime = 5
gRPCRetryCount = 5
gRPCRetryResponse = 'must retry'
gRPCVehicleNoLongerValid = 'vehicle not available'


def write_vehicle_id_mqtt(topic: str, vehicle_id: int, config: EVCCVehicleSocConfiguration):
    try:
        config.vehicle_id = vehicle_id
        value: EVCCVehicleSoc = EVCCVehicleSoc(configuration=config)
        log.debug("saving  vehicle_id: " + str(vehicle_id))
        Pub().pub(topic, asdict(value))
    except Exception as e:
        log.exception('Token mqtt write exception ' + str(e))


def create_vehicle(config: EVCCVehicleSocConfiguration, stub: vehicle_pb2_grpc.VehicleStub) -> int:
    response = stub.New(
        vehicle_pb2.NewRequest(
            token=config.sponsor_token,
            type=config.vehicle_type,
            config=cast(Mapping[str, str], {
                'User': config.user_id,
                'Password': config.password,
                'VIN': config.VIN  # VIN is optional, but must not be None
            })
            )
        )
    return response.vehicle_id


def create_and_save_vehicle_id(
        stub: vehicle_pb2_grpc.VehicleStub,
        config: EVCCVehicleSocConfiguration,
        vehicle: int) -> int:
    vehicle_to_fetch = create_vehicle(config, stub)
    log.debug("Vehicle client received: " + str(vehicle_to_fetch))

    # saving vehicle id in config
    topic = "openWB/set/vehicle/" + str(vehicle) + "/soc_module/config"
    write_vehicle_id_mqtt(topic, vehicle_to_fetch, config)
    return vehicle_to_fetch


def fetch_soc(
    evcc_config: EVCCVehicleSocConfiguration,
    vehicle_update_data: VehicleUpdateData,
    vehicle: int
) -> CarState:
    log.debug("Fetching EVCC SOC")
    with grpc.secure_channel(evcc_endpoint, grpc.ssl_channel_credentials()) as channel:
        stub = vehicle_pb2_grpc.VehicleStub(channel)

        if not evcc_config.vehicle_id:  # create and fetch vehicle id if not included in config
            create_and_save_vehicle_id(stub, evcc_config, vehicle)
#            vehicle_to_fetch = create_vehicle(evcc_config, stub)
#            log.debug("Vehicle client received: " + str(vehicle_to_fetch))

            # saving vehicle id in config
#            topic = "openWB/set/vehicle/" + str(vehicle) + "/soc_module/config"
#            write_vehicle_id_mqtt(topic, vehicle_to_fetch, evcc_config)
        else:
            log.debug("Vehicle id found in config: " + str(evcc_config.vehicle_id))
            vehicle_to_fetch = evcc_config.vehicle_id
        log.debug("Fetching SoC for vehicle id: " + str(vehicle_to_fetch))  # fetch SoC

        RetryCounter = 0
        while RetryCounter < gRPCRetryCount:  # retry fetching SoC if necessary
            try:
                response = stub.SoC(
                    vehicle_pb2.SoCRequest(
                        token=evcc_config.sponsor_token,
                        vehicle_id=vehicle_to_fetch
                    )
                )
                log.debug("SoC received: " + str(response.soc))  # return SoC, exit loop
                break
            except grpc.RpcError as rpc_error:
                if rpc_error.details() == gRPCRetryResponse:  # need to wait and retry
                    log.debug(f"No SoC retrieved, waiting {gRPCRetryTime}s in attempt no {RetryCounter} to retry")
                    time.sleep(gRPCRetryTime)
                    log.debug("retrying now...")
                    RetryCounter += 1
                elif rpc_error.details() == gRPCVehicleNoLongerValid:  # vehicle no longer valid
                    log.debug(f'cached vehicle {vehicle_to_fetch} no longer valid, creating new vehicle')
                    vehicle_to_fetch = create_and_save_vehicle_id(stub, evcc_config, vehicle)
                    RetryCounter += 1
                else:  # some other error, raise exception and exit
                    raise grpc.RpcError(rpc_error)

        if RetryCounter >= gRPCRetryCount:
            raise Exception(f"no SoC received after {gRPCRetryCount} retries with {gRPCRetryTime}s delay")
    return CarState(
        soc=response.soc)
