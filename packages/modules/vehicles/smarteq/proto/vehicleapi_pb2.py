# flake8: noqa
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: vehicleapi.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import modules.vehicles.smarteq.proto.acp_pb2 as acp__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2
import modules.vehicles.smarteq.proto.gogo_pb2 as gogo__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10vehicleapi.proto\x12\x05proto\x1a\tacp.proto\x1a\x1cgoogle/protobuf/struct.proto\x1a\ngogo.proto\"F\n+AcknowledgeAppTwinCommandStatusUpdatesByVIN\x12\x17\n\x0fsequence_number\x18\x01 \x01(\x05\"\xec\x01\n AppTwinCommandStatusUpdatesByVIN\x12\x17\n\x0fsequence_number\x18\x01 \x01(\x05\x12Q\n\x0eupdates_by_vin\x18\x02 \x03(\x0b\x32\x39.proto.AppTwinCommandStatusUpdatesByVIN.UpdatesByVinEntry\x1a\\\n\x11UpdatesByVinEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x36\n\x05value\x18\x02 \x01(\x0b\x32\'.proto.AppTwinCommandStatusUpdatesByPID:\x02\x38\x01\"\xd4\x01\n AppTwinCommandStatusUpdatesByPID\x12\x0b\n\x03vin\x18\x01 \x01(\t\x12Q\n\x0eupdates_by_pid\x18\x02 \x03(\x0b\x32\x39.proto.AppTwinCommandStatusUpdatesByPID.UpdatesByPidEntry\x1aP\n\x11UpdatesByPidEntry\x12\x0b\n\x03key\x18\x01 \x01(\x03\x12*\n\x05value\x18\x02 \x01(\x0b\x32\x1b.proto.AppTwinCommandStatus:\x02\x38\x01\"\x91\x02\n\x14\x41ppTwinCommandStatus\x12\x12\n\nprocess_id\x18\x01 \x01(\x03\x12\x12\n\nrequest_id\x18\x02 \x01(\t\x12\x17\n\x0ftimestamp_in_ms\x18\x03 \x01(\x03\x12&\n\x06\x65rrors\x18\x04 \x03(\x0b\x32\x16.proto.VehicleAPIError\x12!\n\x15\x62locking_time_seconds\x18\x05 \x01(\x03\x42\x02\x18\x01\x12\x18\n\x0cpin_attempts\x18\x06 \x01(\x05\x42\x02\x18\x01\x12$\n\x04type\x18\x07 \x01(\x0e\x32\x16.proto.ACP.CommandType\x12-\n\x05state\x18\x08 \x01(\x0e\x32\x1e.proto.VehicleAPI.CommandState\"\xa2\x01\n\x1bVehicleAPICommandPostResult\x12\x1d\n\nprocess_id\x18\x01 \x01(\x03R\tprocessid\x12.\n\x06\x65rrors\x18\x02 \x03(\x0b\x32\x16.proto.VehicleAPIErrorR\x06\x65rrors\x12\x34\n\x05state\x18\x03 \x01(\x0e\x32\x1e.proto.VehicleAPI.CommandStateR\x05state\"\xba\x01\n\x1aVehicleAPICommandGetResult\x12?\n\x07process\x18\x01 \x03(\x0b\x32%.proto.VehicleAPICommandProcessStatusR\x07process\x12\x1f\n\x0bqueue_count\x18\x02 \x01(\x05R\nqueuecount\x12:\n\nqueue_type\x18\x03 \x01(\x0e\x32\x1b.proto.VehicleAPI.QueueTypeR\tqueuetype\"\xa0\x01\n\x17VehicleAPIDataGetResult\x12\x36\n\x04\x64\x61ta\x18\x01 \x03(\x0b\x32(.proto.VehicleAPIDataGetResult.DataEntry\x1aM\n\tDataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12/\n\x05value\x18\x02 \x01(\x0b\x32 .proto.VehicleAPIAttributeStatus:\x02\x38\x01\"\xa1\x01\n\x19VehicleAPIAttributeStatus\x12,\n\x05value\x18\x03 \x01(\x0b\x32\x16.google.protobuf.ValueR\x05value\x12\x1b\n\x0ftimestamp_in_ms\x18\x02 \x01(\x03R\x02ts\x12\x39\n\x06Status\x18\x01 \x01(\x0e\x32!.proto.VehicleAPI.AttributeStatusR\x06status\"\xe7\x02\n\x1eVehicleAPICommandProcessStatus\x12.\n\x06\x65rrors\x18\x01 \x03(\x0b\x32\x16.proto.VehicleAPIErrorR\x06\x65rrors\x12\x1f\n\x0binstance_id\x18\x02 \x01(\tR\ninstanceid\x12\x12\n\x04name\x18\x03 \x01(\tR\x04name\x12\x1d\n\nprocess_id\x18\x04 \x01(\x03R\tprocessid\x12G\n\x13response_parameters\x18\x06 \x01(\x0b\x32\x16.google.protobuf.ValueR\x12responseparameters\x12\x34\n\x05state\x18\x07 \x01(\x0e\x32\x1e.proto.VehicleAPI.CommandStateR\x05state\x12!\n\x0etimestamp_in_s\x18\x08 \x01(\x03R\ttimestamp\x12\x1f\n\x0btracking_id\x18\t \x01(\tR\ntrackingid\"\x96\x02\n\x0fVehicleAPIError\x12\x18\n\x04\x63ode\x18\x01 \x01(\tR\nerror-code\x12\x1e\n\x07message\x18\x02 \x01(\tR\rerror-message\x12\x46\n\nattributes\x18\x03 \x03(\x0b\x32&.proto.VehicleAPIError.AttributesEntryR\nattributes\x12\x36\n\nsub_errors\x18\x04 \x03(\x0b\x32\x16.proto.VehicleAPIErrorR\nsub-errors\x1aI\n\x0f\x41ttributesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12%\n\x05value\x18\x02 \x01(\x0b\x32\x16.google.protobuf.Value:\x02\x38\x01\"\x1f\n\x1d\x41ppTwinPendingCommandsRequest\"Q\n\x1e\x41ppTwinPendingCommandsResponse\x12/\n\x10pending_commands\x18\x01 \x03(\x0b\x32\x15.proto.PendingCommand\"k\n\x0ePendingCommand\x12\x0b\n\x03vin\x18\x01 \x01(\t\x12\x12\n\nprocess_id\x18\x02 \x01(\x03\x12\x12\n\nrequest_id\x18\x03 \x01(\t\x12$\n\x04type\x18\x04 \x01(\x0e\x32\x16.proto.ACP.CommandTypeB \n\x1a\x63om.daimler.mbcarkit.proto\xd0\xe1\x1e\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'vehicleapi_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n\032com.daimler.mbcarkit.proto\320\341\036\001'
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYVIN_UPDATESBYVINENTRY']._options = None
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYVIN_UPDATESBYVINENTRY']._serialized_options = b'8\001'
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYPID_UPDATESBYPIDENTRY']._options = None
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYPID_UPDATESBYPIDENTRY']._serialized_options = b'8\001'
  _globals['_APPTWINCOMMANDSTATUS'].fields_by_name['blocking_time_seconds']._options = None
  _globals['_APPTWINCOMMANDSTATUS'].fields_by_name['blocking_time_seconds']._serialized_options = b'\030\001'
  _globals['_APPTWINCOMMANDSTATUS'].fields_by_name['pin_attempts']._options = None
  _globals['_APPTWINCOMMANDSTATUS'].fields_by_name['pin_attempts']._serialized_options = b'\030\001'
  _globals['_VEHICLEAPIDATAGETRESULT_DATAENTRY']._options = None
  _globals['_VEHICLEAPIDATAGETRESULT_DATAENTRY']._serialized_options = b'8\001'
  _globals['_VEHICLEAPIERROR_ATTRIBUTESENTRY']._options = None
  _globals['_VEHICLEAPIERROR_ATTRIBUTESENTRY']._serialized_options = b'8\001'
  _globals['_ACKNOWLEDGEAPPTWINCOMMANDSTATUSUPDATESBYVIN']._serialized_start=80
  _globals['_ACKNOWLEDGEAPPTWINCOMMANDSTATUSUPDATESBYVIN']._serialized_end=150
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYVIN']._serialized_start=153
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYVIN']._serialized_end=389
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYVIN_UPDATESBYVINENTRY']._serialized_start=297
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYVIN_UPDATESBYVINENTRY']._serialized_end=389
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYPID']._serialized_start=392
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYPID']._serialized_end=604
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYPID_UPDATESBYPIDENTRY']._serialized_start=524
  _globals['_APPTWINCOMMANDSTATUSUPDATESBYPID_UPDATESBYPIDENTRY']._serialized_end=604
  _globals['_APPTWINCOMMANDSTATUS']._serialized_start=607
  _globals['_APPTWINCOMMANDSTATUS']._serialized_end=880
  _globals['_VEHICLEAPICOMMANDPOSTRESULT']._serialized_start=883
  _globals['_VEHICLEAPICOMMANDPOSTRESULT']._serialized_end=1045
  _globals['_VEHICLEAPICOMMANDGETRESULT']._serialized_start=1048
  _globals['_VEHICLEAPICOMMANDGETRESULT']._serialized_end=1234
  _globals['_VEHICLEAPIDATAGETRESULT']._serialized_start=1237
  _globals['_VEHICLEAPIDATAGETRESULT']._serialized_end=1397
  _globals['_VEHICLEAPIDATAGETRESULT_DATAENTRY']._serialized_start=1320
  _globals['_VEHICLEAPIDATAGETRESULT_DATAENTRY']._serialized_end=1397
  _globals['_VEHICLEAPIATTRIBUTESTATUS']._serialized_start=1400
  _globals['_VEHICLEAPIATTRIBUTESTATUS']._serialized_end=1561
  _globals['_VEHICLEAPICOMMANDPROCESSSTATUS']._serialized_start=1564
  _globals['_VEHICLEAPICOMMANDPROCESSSTATUS']._serialized_end=1923
  _globals['_VEHICLEAPIERROR']._serialized_start=1926
  _globals['_VEHICLEAPIERROR']._serialized_end=2204
  _globals['_VEHICLEAPIERROR_ATTRIBUTESENTRY']._serialized_start=2131
  _globals['_VEHICLEAPIERROR_ATTRIBUTESENTRY']._serialized_end=2204
  _globals['_APPTWINPENDINGCOMMANDSREQUEST']._serialized_start=2206
  _globals['_APPTWINPENDINGCOMMANDSREQUEST']._serialized_end=2237
  _globals['_APPTWINPENDINGCOMMANDSRESPONSE']._serialized_start=2239
  _globals['_APPTWINPENDINGCOMMANDSRESPONSE']._serialized_end=2320
  _globals['_PENDINGCOMMAND']._serialized_start=2322
  _globals['_PENDINGCOMMAND']._serialized_end=2429
# @@protoc_insertion_point(module_scope)