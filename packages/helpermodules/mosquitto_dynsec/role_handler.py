import logging
import re
from typing import Tuple, TypedDict, Optional
from pathlib import Path
from json import load as json_load

from helpermodules.utils.run_command import run_command

VERSION_STRING = "openwb-version:"
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


def _get_packages_path() -> Path:
    return Path(__file__).resolve().parents[3]


def _get_default_roles() -> list[MosquittoRole]:
    with open(_get_packages_path() /
              "data" / "config" / "mosquitto" / "public" / "default-dynamic-security.json", 'r',
              encoding='utf-8') as file:
        dynsec_config = json_load(file)
    roles: list[MosquittoRole] = dynsec_config.get("roles", [])
    return roles if roles else []


def _get_role_templates() -> list[MosquittoRole]:
    with open(_get_packages_path() /
              "data" / "config" / "mosquitto" / "public" / "role-templates.json", 'r', encoding='utf-8') as file:
        roles: list[MosquittoRole] = json_load(file)
    return roles if roles else []


def extract_id_from_role_name(role_name: str) -> Optional[int]:
    numbers = re.findall(r'\d+', role_name)
    if numbers:
        return int(numbers[0])
    return None


def get_acl_role_data(role_template: str, id: int) -> MosquittoRole:
    roles = _get_role_templates()
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


def get_configured_role_data(role_name: str) -> Optional[MosquittoRole]:
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


def list_acl_roles() -> list[str]:
    result = run_command(["mosquitto_ctrl", "dynsec", "listRoles"])
    role_list = result.splitlines()
    return role_list


def acl_role_exists(role_template: str, id: int) -> bool:
    role_data = get_acl_role_data(role_template, id)
    role_list = list_acl_roles()
    return role_data["rolename"] in role_list


def user_exists(username: str) -> Optional[dict]:
    result = run_command(["mosquitto_ctrl", "dynsec", "getClient", username])
    if "not found" in result:
        return False
    return True


def acl_equal_with_placeholder(acl1, acl2):
    def normalize_topic(topic):
        # Ersetze alle /Zahl/ oder /<id>/ durch /<id>/, auch am Ende
        topic = re.sub(r'/\d+/', '/<id>/', topic)
        topic = re.sub(r'/\d+($|/)', r'/<id>\1', topic)
        topic = re.sub(r'/<id>/', '/<id>/', topic)
        topic = re.sub(r'/<id>($|/)', r'/<id>\1', topic)
        return topic
    return (
        acl1["acltype"] == acl2["acltype"] and
        normalize_topic(acl1["topic"]) == normalize_topic(acl2["topic"]) and
        acl1["allow"] == acl2["allow"] and
        acl1["priority"] == acl2["priority"]
    )


def get_acl_versions() -> Tuple[str, str]:
    roles = list_acl_roles()
    dynsec_roles = _get_default_roles()
    for role in roles:
        if VERSION_STRING in role:
            current_version = role.split(":")[1]
            break
    else:
        raise RuntimeError("openwb-version role not found")

    for role in dynsec_roles:
        try:
            if VERSION_STRING in role["rolename"]:
                template_version = role["rolename"].split(":")[1]
                break
        except Exception:
            continue
    else:
        raise RuntimeError("openwb-version role not found in default-dynamic-security.json")

    if current_version != template_version:
        log.info(f"Current ACL version: '{current_version}' Template version: '{template_version}'")
    return current_version, template_version


def get_template_role_data(role_name: str) -> Optional[MosquittoRole]:
    dynsec_roles = _get_default_roles()
    for config_role in dynsec_roles:
        if (config_role["rolename"] == role_name or
                (VERSION_STRING in config_role["rolename"] and VERSION_STRING in role_name)):
            return config_role
    role_templates_config = _get_role_templates()
    for config_role in role_templates_config:
        pattern = config_role["rolename"].replace("<id>", r"\d+")
        if re.match(pattern, role_name):
            return config_role
    return None


def add_acl_role(role_template: str, id: int, force_rewrite: bool = False):
    role_data = get_acl_role_data(role_template, id)

    role_exists = acl_role_exists(role_template, id)
    if role_exists and force_rewrite:
        remove_acl_role(role_template, id)
        role_exists = False
    if role_exists is False:
        log.info(f"Lege fehlende Rolle '{role_data['rolename']}' an.")
        run_command(["mosquitto_ctrl", "dynsec", "createRole", role_data["rolename"]])
        for acl in role_data["acls"]:
            run_command([
                "mosquitto_ctrl", "dynsec", "addRoleAcl", role_data["rolename"],
                acl["acltype"], acl["topic"],
                "allow" if acl["allow"] else "deny",
                str(acl["priority"])
            ])
    else:
        log.debug(f"Rolle '{role_data['rolename']}' existiert bereits und wird nicht erneut angelegt.")


def remove_acl_role(role_template: str, id: int):
    role_data = get_acl_role_data(role_template, id)
    if acl_role_exists(role_template, id):
        log.info(f"Lösche Rolle '{role_data['rolename']}'.")
        run_command(["mosquitto_ctrl", "dynsec", "deleteRole", role_data["rolename"]])
    else:
        log.warning(f"Rolle '{role_data['rolename']}' existiert nicht und kann daher nicht gelöscht werden.")


def update_acls():
    try:
        current_version, template_version = get_acl_versions()
        if current_version != template_version:
            log.info("Aktualisiere ACLs entsprechend der neuen Version...")
            roles = list_acl_roles()
            for role_name in roles:
                try:
                    role_data = get_configured_role_data(role_name)
                    template_role_data = get_template_role_data(role_name)
                    # entferne Rollen, die in der Konfigurationsdatei nicht vorhanden sind
                    # bei allen anderen Rollen dürfen nur die ACLs editiert werden,
                    # damit die Zuordnung zu Benutzern und Gruppen erhalten bleibt!
                    if template_role_data is None:
                        log.info(f"Rolle '{role_data['rolename']}' existiert nicht in den Vorlagen und wird gelöscht.")
                        run_command(["mosquitto_ctrl", "dynsec", "deleteRole", role_data["rolename"]])
                        continue
                    # entferne ACLs aus der Rolle, wenn diese im Template nicht vorhanden sind
                    for acl in role_data["acls"]:
                        for template_acl in template_role_data["acls"]:
                            if acl_equal_with_placeholder(template_acl, acl):
                                break
                        else:
                            log.info(f"Überflüssige ACL {acl['acltype']}:{'allow' if acl['allow'] else 'deny'}:"
                                     f"{acl['topic']}:{acl['priority']} in Rolle {role_data['rolename']} "
                                     "wird entfernt.")
                            run_command([
                                "mosquitto_ctrl", "dynsec", "removeRoleAcl", role_data["rolename"],
                                acl["acltype"], acl["topic"]
                            ])
                    # ergänze zusätzliche ACLs aus dem Template in der Rollen
                    for acl in template_role_data["acls"]:
                        for role_acl in role_data["acls"]:
                            if acl_equal_with_placeholder(acl, role_acl):
                                break
                        else:
                            rolename_id = extract_id_from_role_name(role_data["rolename"])
                            if rolename_id is not None:
                                acl["topic"] = acl["topic"].replace("<id>", str(rolename_id))
                            log.info(f"Zusätzliche ACL {acl['acltype']}:{'allow' if acl['allow'] else 'deny'}:"
                                     f"{acl['topic']}:{acl['priority']} in Rolle {role_data['rolename']} "
                                     "wird hinzugefügt.")
                            run_command([
                                "mosquitto_ctrl", "dynsec", "addRoleAcl", role_data["rolename"],
                                acl["acltype"], acl["topic"],
                                "allow" if acl["allow"] else "deny",
                                str(acl["priority"])
                            ])
                except Exception:
                    log.exception(f"Fehler beim Aktualisieren der Rolle '{role_name}'")
            # Rollen ergänzen, welche in der neuen Version hinzugekommen sind,
            # aber noch nicht in der Konfiguration existieren
            dynsec_roles = _get_default_roles()
            for config_role in dynsec_roles:
                if (config_role["rolename"] not in roles and
                        VERSION_STRING not in config_role["rolename"]):
                    log.info(f"Füge neue Rolle '{config_role['rolename']}' aus der neuen Version hinzu.")
                    run_command(["mosquitto_ctrl", "dynsec", "createRole", config_role["rolename"]])
                    for acl in config_role["acls"]:
                        run_command([
                            "mosquitto_ctrl", "dynsec", "addRoleAcl", config_role["rolename"],
                            acl["acltype"], acl["topic"],
                            "allow" if acl["allow"] else "deny",
                            str(acl["priority"])
                        ])
            # aktualisiere die openwb-version Rolle
            run_command(["mosquitto_ctrl", "dynsec", "deleteRole", f"{VERSION_STRING}{current_version}"])
            run_command(["mosquitto_ctrl", "dynsec", "createRole", f"{VERSION_STRING}{template_version}"])
            log.info("ACL-Aktualisierung abgeschlossen.")
    except Exception:
        log.exception("Fehler beim Aktualisieren der ACLs")
