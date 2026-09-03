import importlib
from typing import Any

from dataclass_utils import dataclass_from_dict


def deserialize_display_theme(config: dict[str, Any]) -> Any:
    if not isinstance(config, dict):
        raise ValueError("Die Display-Theme-Konfiguration muss ein JSON-Objekt sein.")

    theme_type = config.get("type")
    if not isinstance(theme_type, str) or not theme_type.isidentifier():
        raise ValueError("Der Typ des Display-Themes fehlt.")
    if "configuration" in config and not isinstance(config["configuration"], dict):
        raise ValueError("Die Konfiguration des Display-Themes muss ein JSON-Objekt sein.")

    module_name = f"modules.display_themes.{theme_type}.config"
    try:
        module = importlib.import_module(f".{theme_type}.config", "modules.display_themes")
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise
        raise ValueError(f"Unbekanntes Display-Theme: {theme_type}") from exc

    theme = dataclass_from_dict(module.theme_descriptor.configuration_factory, config)
    default_theme = module.theme_descriptor.configuration_factory()
    if not isinstance(theme.configuration, type(default_theme.configuration)):
        raise ValueError("Die Konfiguration des Display-Themes hat einen ungültigen Typ.")
    return theme
