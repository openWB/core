from json import load as json_load
import json
import logging
from pathlib import Path
import re
from typing import Tuple, TypedDict, Optional

from helpermodules.subdata import SubData
from helpermodules.utils.run_command import run_command

log = logging.getLogger(__name__)


class MosquittoAcl(TypedDict):
    acltype: str
    topic: str
    allow: bool
    priority: int

    def __eq__(self, other):
        if self["acltype"] == other["acltype"]:
            if re.sub(r'/\d+/', '/<id>/', self["topic"]) == re.sub(r'/\d+/', '/<id>/', other["topic"]):
                if self["allow"] == other["allow"]:
                    if self["priority"] == other["priority"]:
                        return True
            return False


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
    update_acls()
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


def _extract_id_from_role_name(role_name: str) -> Optional[int]:
    numbers = re.findall(r'\d+', role_name)
    if numbers:
        return int(numbers[0])
    return None


def _get_configured_role_data(role_name: str) -> Optional[MosquittoRole]:
    role_output = run_command([
        "mosquitto_ctrl", "dynsec", "getRole", role_name])
    # Parse the text output since it's not JSON
    role_data = {"rolename": role_name, "acls": []}
    lines = role_output.strip().split('\n')
    for line in lines[1:]:  # Skip first line with rolename
        if "ACLs:" in line:
            line = line.replace("ACLs:", "")
        if line.strip() and ':' in line:
            parts = [p.strip() for p in line.split(':')]
            if len(parts) >= 4:
                acl = {
                    "acltype": parts[0],
                    "allow": parts[1] == "allow",
                    "topic": parts[2].split('(')[0].strip(),
                    "priority": int(parts[3].replace(')', '').strip())
                }
                role_data["acls"].append(acl)
    return role_data


VERSION_STRING = "openwb-version:"


def update_acls():
    def get_acl_versions() -> Tuple[str, str]:
        for role in roles:
            if VERSION_STRING in role:
                current_version = role.split(":")[1]
                break
        else:
            raise RuntimeError("openwb-version role not found")

        for role in dynsec_config["roles"]:
            try:
                if VERSION_STRING in role["rolename"]:
                    template_version = role["rolename"].split(":")[1]
                    break
            except Exception:
                continue
        else:
            raise RuntimeError("openwb-version role not found in default-dynamic-security.json")

        if current_version != template_version:
            log.debug(f"Current ACL version: '{current_version}' Template version: '{template_version}'")
        return current_version, template_version

    def get_template_role_data() -> Optional[MosquittoRole]:
        for config_role in dynsec_config["roles"]:
            if (config_role["rolename"] == role_data["rolename"] or
                    (VERSION_STRING in config_role["rolename"] and VERSION_STRING in role_data["rolename"])):
                return config_role
        for config_role in role_templates_config:
            pattern = config_role["rolename"].replace("<id>", r"\d+")
            if re.match(pattern, role_data["rolename"]):
                return config_role
        raise RuntimeError(f"Role {role_data['rolename']} not found in default-dynamic-security.json")

    try:
        roles = _list_acl_roles()
        with open(_get_packages_path()/"data/config/mosquitto/public/default-dynamic-security.json", "r") as f:
            dynsec_config = json.load(f)
        current_version, template_version = get_acl_versions()
        if current_version != template_version:
            with open(_get_packages_path()/"data/config/mosquitto/public/role-templates.json", "r") as f:
                role_templates_config = json.load(f)
            for role_name in roles:
                try:
                    role_data = _get_configured_role_data(role_name)
                    template_role_data = get_template_role_data()
                    if template_role_data:
                        # vegleiche die zwei ACL dicts, welche ACLs hinzugefügt, geändert oder entfernt wurden
                        for acl in role_data["acls"]:
                            for template_acl in template_role_data["acls"]:
                                if template_acl == acl:
                                    break
                            else:
                                log.debug(f"ACL {acl['acltype']}:{'allow' if acl['allow'] else 'deny'}:{acl['topic']}:"
                                          f"{acl['priority']} in Rolle {role_data['rolename']} wird entfernt.")
                                run_command([
                                    "mosquitto_ctrl", "dynsec", "removeRoleAcl", role_data["rolename"],
                                    acl["acltype"], acl["topic"]
                                ])
                        for acl in template_role_data["acls"]:
                            for role_acl in role_data["acls"]:
                                if acl == role_acl:
                                    break
                            else:
                                rolename_id = _extract_id_from_role_name(role_data["rolename"])
                                if rolename_id is not None:
                                    acl["topic"] = acl["topic"].replace("<id>", str(rolename_id))
                                log.debug(f"ACL {acl['acltype']}:{'allow' if acl['allow'] else 'deny'}:{acl['topic']}:"
                                          f"{acl['priority']} in Rolle {role_data['rolename']} wird hinzugefügt.")
                                run_command([
                                    "mosquitto_ctrl", "dynsec", "addRoleAcl", role_data["rolename"],
                                    acl["acltype"], acl["topic"],
                                    "allow" if acl["allow"] else "deny",
                                    str(acl["priority"])
                                ])
                    elif template_role_data is None:
                        log.debug(f"Rolle '{role_data['rolename']}' existiert nicht in den Konfigurationsdateien und"
                                  " wird gelöscht.")
                        run_command(["mosquitto_ctrl", "dynsec", "deleteRole", role_data["rolename"]])
                except Exception:
                    log.exception(f"Fehler beim Aktualisieren der Rolle '{role_name}'")
            # bei allen anderen Rollen dürfen nur die ACLs editiert werden,
            # damit diese in den Benutzergruppen erhalten bleiben
            run_command(["mosquitto_ctrl", "dynsec", "deleteRole", f"{VERSION_STRING}{current_version}"])
            run_command(["mosquitto_ctrl", "dynsec", "createRole", f"{VERSION_STRING}{template_version}"])
    except Exception:
        log.exception("Fehler beim Aktualisieren der ACLs")


def _get_packages_path() -> Path:
    return Path(__file__).resolve().parents[2]
