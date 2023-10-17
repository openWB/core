import logging
import pickle
import json
import paho.mqtt.publish as publish
import msal
import base64

from helpermodules.messaging import MessageType
from modules.backup_clouds.onedrive.config import OneDriveBackupCloud, OneDriveBackupCloudConfiguration


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


def generateMSALAuthCode(cloudbackup: OneDriveBackupCloud) -> dict:
    """ startet den Authentifizierungsprozess für MSAL (Microsoft Authentication Library) für Onedrive Backup
    und speichert den AuthCode in der Konfiguration"""
    result = dict(
        message="",
        MessageType=MessageType.SUCCESS
    )

    if cloudbackup is None:
        result["message"] = """Es ist keine Backup-Cloud konfiguriert.
                            Bitte Konfiguration speichern und erneut versuchen.<br />"""
        result["MessageType"] = MessageType.WARNING
        return result

    # Create a public client application with msal
    app = msal.PublicClientApplication(
        client_id=cloudbackup.configuration.clientID,
        authority=cloudbackup.configuration.authority
        )

    # create device flow to obtain auth code
    flow = app.initiate_device_flow(cloudbackup.configuration.scope)
    if "user_code" not in flow:
        raise Exception(
            "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

    flow["expires_at"] = 0  # Mark it as expired immediately to prevent
    pickleString = str(pickle.dumps(flow), encoding='latin1')

    cloudbackup.configuration.flow = str(pickleString)
    cloudbackup.configuration.authcode = flow["user_code"]
    cloudbackup.configuration.authurl = flow["verification_uri"]
    cloudbackupconfig_to_mqtt = json.dumps(cloudbackup.__dict__, default=lambda o: o.__dict__)

    publish.single(
        "openWB/set/system/backup_cloud/config", cloudbackupconfig_to_mqtt, retain=True, hostname="localhost"
        )

    result["message"] = """Authorisierung gestartet, bitte den Link öffen, Code eingeben,
        und Zugang authorisieren. Anschließend Zugangsberechtigung abrufen."""
    result["MessageType"] = MessageType.SUCCESS

    return result


def retrieveMSALTokens(cloudbackup: OneDriveBackupCloud) -> dict:
    result = dict(
        message="",
        MessageType=MessageType.SUCCESS
    )
    if cloudbackup is None:
        result["message"] = """Es ist keine Backup-Cloud konfiguriert.
                            Bitte Konfiguration speichern und erneut versuchen.<br />"""
        result["MessageType"] = MessageType.WARNING
        return result

    # Create a public client application with msal
    tokens = None
    cache = msal.SerializableTokenCache()
    app = msal.PublicClientApplication(client_id=cloudbackup.configuration.clientID,
                                       authority=cloudbackup.configuration.authority, token_cache=cache)

    f = cloudbackup.configuration.flow
    if f is None:
        result["message"] = """Es ist wurde kein Auth-Code erstellt.
                            Bitte zunächst Auth-Code erstellen und den Authorisierungsprozess beenden.<br />"""
        result["MessageType"] = MessageType.WARNING
        return result
    flow = pickle.loads(bytes(f, encoding='latin1'))

    tokens = app.acquire_token_by_device_flow(flow)
    # https://msal-python.readthedocs.io/en/latest/#msal.PublicClientApplication.acquire_token_by_device_flow
    # https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-device-code
    # Check if the token was obtained successfully
    if "access_token" in tokens:
        log.debug("retrieved access token")

        # Tokens retrieved, remove auth codes as they are single use only.
        cloudbackup.configuration.flow = None
        cloudbackup.configuration.authcode = None
        cloudbackup.configuration.authurl = None

        # save tokens
        save_tokencache(config=cloudbackup.configuration, cache=cache.serialize())
        result["message"] = """Zugangsberechtigung erfolgreich abgerufen."""
        result["MessageType"] = MessageType.SUCCESS
        return result

    else:
        result["message"] = """"Es konnten keine Tokens abgerufen werden:
                            %s <br> %s""" % (tokens.get("error"), tokens.get("error_description"))
        result["MessageType"] = MessageType.WARNING
        '''pub_user_message(payload, connection_id,
                            "Es konnten keine Tokens abgerufen werden: %s <br> %s"
                            % (result.get("error"), result.get("error_description")), MessageType.WARNING
                            )
        '''
        return result
