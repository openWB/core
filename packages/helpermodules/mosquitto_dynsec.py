from json import load as json_load
import logging
from pathlib import Path
from typing import TypedDict, Optional

from helpermodules.subdata import SubData
from helpermodules.utils.run_command import run_command

log = logging.getLogger(__name__)


class MosquittoAcl(TypedDict):
    acltype: str
    topic: str
    allow: bool
    priority: int


class MosquittoRole(TypedDict):
    rolename: str
    textname: Optional[str]
    textdescription: Optional[str]
    acls: list[MosquittoAcl]


def _get_acl_role_data(role_template: str, id: int) -> MosquittoRole:
    with open(Path(__file__).resolve().parents[2] /
              "data" / "config" / "mosquitto" / "public" / "role-templates.json", 'r', encoding='utf-8') as file:
        roles: list[MosquittoRole] = json_load(file)
    role_data = None
    for role in roles:
        if role["rolename"] == role_template:
            role_data = role
            break
    if role_data is None:
        raise ValueError(f"Kein passendes Rollen-Template für '{role_template}' gefunden.")
    role_data["rolename"] = role_data["rolename"].replace("<id>", str(id))
    role_data["textname"] = role_data["textname"].replace("<id>", str(id))
    role_data["textdescription"] = role_data["textdescription"].replace("<id>", str(id))
    for acl in role_data["acls"]:
        acl["topic"] = acl["topic"].replace("<id>", str(id))
    return role_data


def _list_acl_roles() -> list[str]:
    result = run_command(["mosquitto_ctrl", "dynsec", "listRoles"])
    role_list = result.splitlines()
    return role_list


def _acl_role_exists(role_template: str, id: int) -> bool:
    role_data = _get_acl_role_data(role_template, id)
    role_list = _list_acl_roles()
    return role_data["rolename"] in role_list


def add_acl_role(role_template: str, id: int, force_rewrite: bool = False):
    role_data = _get_acl_role_data(role_template, id)

    role_exists = _acl_role_exists(role_template, id)
    if role_exists and force_rewrite:
        remove_acl_role(role_template, id)
        role_exists = False
    if role_exists is False:
        run_command(["mosquitto_ctrl", "dynsec", "createRole", role_data["rolename"]])
        for acl in role_data["acls"]:
            run_command([
                "mosquitto_ctrl", "dynsec", "addRoleAcl", role_data["rolename"],
                acl["acltype"], acl["topic"],
                "allow" if acl["allow"] else "deny",
                str(acl["priority"])
            ])
    else:
        log.warning(f"Rolle '{role_data['rolename']}' existiert bereits und wird nicht erneut angelegt.")


def remove_acl_role(role_template: str, id: int):
    role_data = _get_acl_role_data(role_template, id)
    if _acl_role_exists(role_template, id):
        run_command(["mosquitto_ctrl", "dynsec", "deleteRole", role_data["rolename"]])
    else:
        log.warning(f"Rolle '{role_data['rolename']}' existiert nicht und kann daher nicht gelöscht werden.")


def check_roles_at_start():
    flag_path = Path(Path(__file__).resolve().parents[2]/"ramdisk"/"init_user_management")
    if flag_path.is_file():
        with open(flag_path, "r") as file:
            flag = bool(file.read())
        if flag:
            for cp in SubData.cp_data.values():
                add_acl_role("chargepoint-<id>-access", cp.chargepoint.num)
            for ev in SubData.ev_data.values():
                add_acl_role("vehicle-<id>-access", ev.num)
            for bat in SubData.bat_data.values():
                add_acl_role("bat-<id>-access", bat.num)
            for counter in SubData.counter_data.values():
                add_acl_role("counter-<id>-access", counter.num)
            for inverter in SubData.pv_data.values():
                add_acl_role("inverter-<id>-access", inverter.num)
            for io_action in SubData.io_actions.actions.values():
                add_acl_role("io-action-<id>-access", io_action.config.id)
            for key, value in SubData.system_data.items():
                if "io" in key:
                    add_acl_role("io-device-<id>-access", value.config.id)
        flag_path.unlink()
