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

log = logging.getLogger(__name__)

# Define the scope of access
scope = ["https://graph.microsoft.com/Files.ReadWrite"]

# Define the authority and the token endpoint for MSA/Live accounts
authority = "https://login.microsoftonline.com/consumers/"
clientID = "e529d8d2-3b0f-4ae4-b2ba-2d9a2bba55b2"


# to-do move into one or more functions
def get_tokens(persistent_tokencache: str) -> dict:
    result = None
    cache = msal.SerializableTokenCache()

    # to-do: add write to config after update
    '''if os.path.exists("my_cache.bin"):  # to do: read from config
        cache.deserialize(open("my_cache.bin", "r").read())
    atexit.register(lambda: open("my_cache.bin", "w").write(cache.serialize())  # to-do: write to config
                    if cache.has_state_changed else None
                    )
'''
    if persistent_tokencache:
        cache.deserialize(persistent_tokencache)

    # Create a public client application with msal
    app = msal.PublicClientApplication(client_id=clientID, authority=authority, token_cache=cache)

    accounts = app.get_accounts()
    if accounts:
        chosen = accounts[0]  # assume that we only will have a single account in cache
        # Now let's try to find a token in cache for this account
        result = app.acquire_token_silent(scopes=scope, account=chosen)

    if not result:  # We have no token for this account, so the end user shall sign-in

        flow = app.initiate_device_flow(scope)
        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

        print(flow["message"])  # to-do: present to user, open in browser and ask to sign in

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


def upload_backup(config: OneDriveBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    # upload a single file to onedrive useing credentials from OneDriveBackupCloudConfiguration
    # https://docs.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_put_content?view=odsp-graph-online
    # to-do: acquire tokens
    tokens = get_tokens(config.tokencache)
    log.debug("token object retrieved, access_token: %s", tokens.access_token)
    onedrive = OneDrive(access_token=tokens.access_token)
    log.debug("instantiated OneDrive object")
    onedrive.upload_item(item_path=config.backuppath+backup_filename, file_path=backup_filename,
                         conflict_behavior="replace")
    log.debug("uploaded file %s to OneDrive", backup_filename)


def create_backup_cloud(config: OneDriveBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return ConfigurableBackupCloud(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=OneDriveBackupCloud)
