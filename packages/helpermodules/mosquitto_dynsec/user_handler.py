import logging
from secrets import token_hex
from typing import Optional, Tuple
from json import dump as json_dump

from helpermodules.mosquitto_dynsec.role_handler import _get_packages_path
from helpermodules.utils.run_command import run_command

USER_CREDENTIALS_PATH = _get_packages_path() / "data" / "clients"
log = logging.getLogger(__name__)


def store_user_credentials(file_name: str, user_name: str, password: str) -> None:
    credentials_file = USER_CREDENTIALS_PATH / f"{file_name}.json"
    credentials_file.parent.mkdir(parents=True, exist_ok=True)
    with open(credentials_file, "w") as file:
        json_dump({"username": user_name, "password": password}, file, indent=4)


def remove_user_credentials(file_name: str) -> None:
    credentials_file = USER_CREDENTIALS_PATH / f"{file_name}.json"
    if credentials_file.is_file():
        credentials_file.unlink()


def add_user_to_group(username: str, groupname: str) -> None:
    run_command(["mosquitto_ctrl", "dynsec", "addGroupClient", groupname, username])


def create_display_user(ip_address: str, user_name: Optional[str] = None) -> Tuple[bool, str]:
    if user_name is None:
        user_name = f"Display-{ip_address}"
    file_name = f"display-{ip_address}".replace('.', '_')
    if user_exists(user_name):
        log.info(f"User '{user_name}' already exists")
        return True, user_name
    password = token_hex(16)
    if not add_user(user_name, password):
        log.error(f"Failed to create user '{user_name}' for cp display at {ip_address}")
        return False, user_name
    add_user_to_group(user_name, "display")
    store_user_credentials(
        file_name,
        user_name,
        password
    )
    log.info(f"Created user '{user_name}' for cp display at {ip_address}")
    return True, user_name


def remove_display_user(ip_address: str) -> bool:
    user_name = f"Display-{ip_address}"
    if remove_user(user_name):
        remove_user_credentials(user_name.lower().replace('.', '_'))
        log.info(f"Removed user '{user_name}' for cp display at {ip_address}")
        return True
    log.error(f"Failed to remove user '{user_name}' for cp display at {ip_address}")
    return False


def user_exists(username: str) -> Optional[dict]:
    result = run_command(["mosquitto_ctrl", "dynsec", "getClient", username], process_exception=True)
    if username in result:
        return True
    return False


def add_user(username: str, password: str) -> bool:
    if not user_exists(username):
        run_command(["mosquitto_ctrl", "dynsec", "createClient", username, "-p", password])
        return True
    return False


def remove_user(username: str) -> bool:
    if user_exists(username):
        run_command(["mosquitto_ctrl", "dynsec", "deleteClient", username])
        return True
    return False


def update_user_password(username: str, new_password: str) -> bool:
    if user_exists(username):
        run_command(["mosquitto_ctrl", "dynsec", "setClientPassword", username, new_password])
        return True
    return False
