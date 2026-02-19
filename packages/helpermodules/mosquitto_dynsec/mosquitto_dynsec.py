import logging
import re
import requests
from json import load as json_load, dump as json_dump
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from secrets import token_hex

from helpermodules.subdata import SubData
from helpermodules.utils.run_command import run_command
from helpermodules.mosquitto_dynsec.role_handler import add_acl_role, update_acls
from helpermodules.mosquitto_dynsec.user_handler import create_display_user, user_exists
from modules.common.component_type import special_to_general_type_mapping

TOKEN_DATA_PATH = Path(Path(__file__).resolve().parents[2]/"ramdisk"/"password_reset_tokens")

log = logging.getLogger(__name__)


def get_user_email(username: str) -> Optional[str]:
    email_regexp = r'(^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9]{2,7}$)'
    if user_exists(username):
        result = run_command(["/var/www/html/openWB/runs/dynsec_helper/get_user_mail.sh", username])
        email = result.strip()
        return email if re.fullmatch(email_regexp, email) else None
    return None


def generate_password_reset_token(username: str) -> list[str, int]:
    token = token_hex(16)
    token_hash = bcrypt.hash(token)
    expires_at = datetime.now() + timedelta(hours=1)

    TOKEN_DATA_PATH.mkdir(parents=True, exist_ok=True)
    token_file = TOKEN_DATA_PATH / f"{username}_reset.token"
    with open(token_file, "w") as file:
        # store hash and timestamp in epoch format
        json_dump({"token_hash": token_hash, "expires_at": int(expires_at.timestamp())}, file)
    return token, int(expires_at.timestamp())


def send_password_reset_to_server(email: str, token: str, expires_at: int) -> None:
    TOKEN_SERVER_URL = "https://openwb.de/forgotpassword/send_token.php"
    timeout = 10  # seconds
    payload = {
        "email": email,
        "subject": "openWB Passwort zurücksetzen",
        "message": (f"Hallo,\n\n"
                    "es wurde ein Antrag zum Zurücksetzen deines openWB Passworts gestellt.\n"
                    "Bitte benutze das folgende Token, um dein Passwort zurückzusetzen:\n\n"
                    f"{token}\n\n"
                    "Das Token ist gültig bis "
                    f"{datetime.fromtimestamp(expires_at).strftime('%d.%m.%Y %H:%M:%S %Z')}.\n\n"
                    "Falls du Dein Passwort nicht zurücksetzen wolltest, kannst du diese E-Mail ignorieren.")
    }
    error: Optional[str] = None
    response: Optional[requests.Response] = None
    try:
        response = requests.post(
            url=TOKEN_SERVER_URL,
            json=payload,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'User-Agent': 'Token-Client/1.0',
            },
            timeout=timeout,
            verify=True
        )
        print(f"{response.status_code}: {response.text}")
    except requests.exceptions.Timeout:
        error = f"Error: request timed out after {timeout}s"
    except requests.exceptions.ConnectionError:
        error = f"Error: connection to {TOKEN_SERVER_URL} failed"
    except requests.RequestException as e:
        error = f"HTTP-Error: {e}"
    if error is not None or response.status_code != 200:
        print(f"Failed to send password reset email: {error or f'status {response.status_code}'}")


def verify_password_reset_token(username: str, token: str) -> bool:
    token_file = TOKEN_DATA_PATH / f"{username}_reset.token"
    if not token_file.is_file():
        return False
    with open(token_file, "r") as file:
        token_data = json_load(file)
    expires_at = token_data["expires_at"]
    if datetime.now().timestamp() > expires_at:
        token_file.unlink()
        return False
    token_hash = token_data["token_hash"]
    if bcrypt.verify(token, token_hash):
        token_file.unlink()
        return True
    return False


def check_required_users():
    def create_user(ip_address: str):
        success, user_name = create_display_user(ip_address, user_name="Display-Intern")
        if success:
            log.info(f"Created user '{user_name}' for cp display at {ip_address}")
        else:
            log.error(f"Failed to create user for cp display at {ip_address}")

    # Always create user for localhost to ensure access to local displays, even if no chargepoints are configured
    create_user("127.0.0.1")
    # Create users for chargepoints of type 'external_openwb'
    for cp in SubData.cp_data.values():
        cp_type = cp.chargepoint.data.config.type
        if cp_type == "external_openwb":
            ip_address: Optional[str] = cp.chargepoint.data.config.configuration.get('ip_address')
        else:
            log.info(f"Chargepoint {cp.chargepoint.num} has type '{cp_type}', skipping user creation")
            continue
        if ip_address is None:
            log.warning(f"No IP address configured for cp {cp.chargepoint.num}, skipping user creation")
            continue
        create_user(ip_address)


def check_roles_at_start():
    update_acls()
    flag_path = Path(Path(__file__).resolve().parents[3]/"ramdisk"/"init_user_management")
    if flag_path.is_file():
        with open(flag_path, "r") as file:
            flag = bool(file.read())
        if flag:
            for cp in SubData.cp_data.values():
                add_acl_role("chargepoint-<id>-access", cp.chargepoint.num)
                if cp.chargepoint.data.config.type == "mqtt":
                    add_acl_role("chargepoint-<id>-write-access", cp.chargepoint.num)
            for ev in SubData.ev_data.values():
                add_acl_role("vehicle-<id>-access", ev.num)
                if ev.soc_module is not None and ev.soc_module.vehicle_config.type == "mqtt":
                    add_acl_role("vehicle-<id>-write-access", ev.num)
            for io_action in SubData.io_actions.actions.values():
                add_acl_role("io-action-<id>-access", io_action.config.id)
            for key, value in SubData.system_data.items():
                if "device" in key:
                    for component in value.components.values():
                        general_type = special_to_general_type_mapping(component.component_config.type).value
                        add_acl_role(f"{general_type}-<id>-access", component.component_config.id)
                        if value.device_config.type == "mqtt":
                            add_acl_role(f"{general_type}-<id>-write-access", component.component_config.id)
                if "io" in key:
                    add_acl_role("io-device-<id>-access", value.config.id)
                    if value.config.output["digital"] or value.config.output["analog"]:
                        add_acl_role("io-device-<id>-write-access", value.config.id)
        flag_path.unlink()
    check_required_users()
