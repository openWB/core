#!/usr/bin/env python3
import logging
import msal
import os
import json
from msdrive import OneDrive
import paho.mqtt.publish as publish
from modules.backup_clouds.onedrive.config import OneDriveBackupCloud, OneDriveBackupCloudConfiguration
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud
import pathlib
import base64


log = logging.getLogger(__name__)


def encode_str_base64(string: str) -> str:
    string_bytes = string.encode("ascii")
    string_base64_bytes = base64.b64encode(string_bytes)
    string_base64_string = string_base64_bytes.decode("ascii")
    return string_base64_string


def save_tokencache(config: OneDriveBackupCloudConfiguration, cache: str) -> None:
    # encode cache to base64 and save to config
    log.debug("saving updated tokencache to config")
    config.persistent_tokencache = encode_str_base64(cache)

    # construct full configuartion object for cloud backup
    backupcloud = OneDriveBackupCloud()
    backupcloud.configuration = config
    backupcloud_to_mqtt = json.dumps(backupcloud.__dict__, default=lambda o: o.__dict__)
    log.debug("Config to MQTT:" + str(backupcloud_to_mqtt))

    publish.single("openWB/set/system/backup_cloud/config", backupcloud_to_mqtt, retain=True, hostname="localhost")


def get_tokens(config: OneDriveBackupCloudConfiguration) -> dict:
    result = None
    cache = msal.SerializableTokenCache()

    if config.persistent_tokencache:
        cache.deserialize(base64.b64decode(config.persistent_tokencache))
    else:
        raise Exception("No tokencache found, please re-configure and re-authorize access Cloud backup settings.")

    # Create a public client application with msal
    log.debug("creating MSAL public client application")
    app = msal.PublicClientApplication(client_id=config.clientID, authority=config.authority, token_cache=cache)

    log.debug("getting accounts")
    accounts = app.get_accounts()
    if accounts:
        chosen = accounts[0]  # assume that we only will have a single account in cache
        log.debug("selected account " + str(chosen["username"]))
        # Now let's try to find a token in cache for this account
        result = app.acquire_token_silent(scopes=config.scope, account=chosen)
    else:
        raise Exception("No matching account found,please re-configure and re-authorize access Cloud backup settings.")

    log.debug("done acquring tokens")
    if not result:  # We have no token for this account, so the end user shall sign-in
        raise Exception("No token found, please re-configure and re-authorize access Cloud backup settings.")

    if "access_token" in result:
        log.debug("access token retrieved")
        save_tokencache(config=config, cache=cache.serialize())
    else:
        # Print the error
        raise Exception("Error retrieving access token", result.get("error"), result.get("error_description"))
    return result


def upload_backup(config: OneDriveBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    # upload a single file to onedrive useing credentials from OneDriveBackupCloudConfiguration
    # https://docs.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_put_content?view=odsp-graph-online
    tokens = get_tokens(config)  # type: ignore
    log.debug("token object retrieved, access_token: %s", tokens.__len__)
    log.debug("instantiate OneDrive connection")
    onedrive = OneDrive(access_token=tokens["access_token"])

    localbackup = os.path.join(pathlib.Path().resolve(), 'data', 'backup', backup_filename)
    remote_filename = backup_filename.replace(':', '-')  # file won't upload when name contains ':'

    if not config.backuppath.endswith("/"):
        log.debug("fixing  missing ending slash in backuppath: " + config.backuppath)
        config.backuppath = config.backuppath + "/"

    log.debug("uploading file %s to OneDrive", backup_filename)
    onedrive.upload_item(item_path=(config.backuppath+remote_filename), file_path=localbackup,
                         conflict_behavior="replace")


def create_backup_cloud(config: OneDriveBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return ConfigurableBackupCloud(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=OneDriveBackupCloud)
