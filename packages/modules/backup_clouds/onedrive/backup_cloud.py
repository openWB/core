#!/usr/bin/env python3
import logging
import msal
import atexit
import os
import json
from msdrive import OneDrive
from modules.backup_clouds.onedrive.config import OneDriveBackupCloud, OneDriveBackupCloudConfiguration
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud
import pathlib
import base64


log = logging.getLogger(__name__)


def get_tokens(config: OneDriveBackupCloudConfiguration) -> dict:
    result = None
    cache = msal.SerializableTokenCache()

    '''    # to-do: add write to config after update
    if os.path.exists("/var/www/html/openWB/packages/modules/backup_clouds/onedrive/my_cache.bin"):  # to do: read from config
        log.debug("reading token cache from file")
        cache.deserialize(open("/var/www/html/openWB/packages/modules/backup_clouds/onedrive/my_cache.bin", "r").read())
    else:
        log.debug("token cache not found")
    atexit.register(lambda: open("my_cache.bin", "w").write(cache.serialize())  # to-do: write to config
                    if cache.has_state_changed else None
                    )'''

    if config.persistent_tokencache:
        cache.deserialize(base64.b64decode(config.persistent_tokencache))

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

    log.debug("done acquring tokens")
    if not result:  # We have no token for this account, so the end user shall sign-in
        # to-do: stop execution if no authcode is provided, log error

        flow = app.initiate_device_flow(config.scope)

        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

        log.debug(flow["message"])  # to-do: present to user, open in browser and ask to sign in

        # Ideally you should wait here, in order to save some unnecessary polling
        # input("Press Enter after signing in from another device to proceed, CTRL+C to abort.")

        result = app.acquire_token_by_device_flow(flow)  # By default it will block
        # You can follow this instruction to shorten the block time
        #    https://msal-python.readthedocs.io/en/latest/#msal.PublicClientApplication.acquire_token_by_device_flow
        # or you may even turn off the blocking behavior,
        # and then keep calling acquire_token_by_device_flow(flow) in your own customized loop

    # Check if the token was obtained successfully
    if "access_token" in result:
        # Print the access token
        print(result["access_token"])
    else:
        # Print the error
        print(result.get("error"), result.get("error_description"))
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
