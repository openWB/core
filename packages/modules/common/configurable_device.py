import inspect
import logging
from typing import TypeVar, Generic, Dict, Any, Callable, Iterable, List

from dataclass_utils import dataclass_from_dict
from helpermodules import timecheck
from helpermodules.pub import Pub
from modules.common.abstract_device import AbstractDevice
from modules.common.component_context import SingleComponentUpdateContext, MultiComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState

T_DEVICE_CONFIG = TypeVar("T_DEVICE_CONFIG")
T_COMPONENT = TypeVar("T_COMPONENT")
T_COMPONENT_CONFIG = TypeVar("T_COMPONENT_CONFIG")

ComponentUpdater = Callable[[Iterable[T_COMPONENT]], None]
ComponentFactory = Callable[[T_COMPONENT_CONFIG], T_COMPONENT]

log = logging.getLogger(__name__)


class IndependentComponentUpdater(Generic[T_COMPONENT]):
    def __init__(self, updater: Callable[[T_COMPONENT], None]):
        self.__updater = updater

    def __call__(self, components: Iterable[T_COMPONENT], error_handler: Callable) -> None:
        # error_handler nur einmal ausführen, da er für das ganze Gerät gilt
        run_error_handler = False
        for component in components:
            try:
                with SingleComponentUpdateContext(component.fault_state, reraise=True):
                    self.__updater(component)
            except Exception:
                run_error_handler = True
        if run_error_handler:
            error_handler()


class MultiComponentUpdater:
    def __init__(self, updater: Callable[[List[T_COMPONENT]], None]):
        self.__updater = updater

    def __call__(self, components: Iterable[T_COMPONENT], error_handler: Callable) -> None:
        components_list = list(components)
        with MultiComponentUpdateContext(components_list, error_handler):
            if not components:
                raise Exception("Keine Komponenten konfiguriert oder Initialisierung fehlgeschlagen")
            self.__updater(components_list)


class ComponentFactoryByType(Generic[T_COMPONENT, T_COMPONENT_CONFIG]):
    def __init__(self, **type_to_factory: ComponentFactory[Any, T_COMPONENT]):
        self.__type_to_factory = type_to_factory

    def __call__(self, component_config: T_COMPONENT_CONFIG) -> T_COMPONENT:
        component_type = component_config["type"] if isinstance(component_config, dict) else component_config.type
        try:
            factory = self.__type_to_factory[component_type]
        except KeyError as e:
            raise Exception(
                "Unknown component type <%s>, known types are: <%s>", e, ','.join(self.__type_to_factory.keys())
            )
        arg_spec = inspect.getfullargspec(factory)
        if len(arg_spec.args) != 1:
            raise Exception(
                "Expected function with single argument, however factory for %s has args: %s" %
                (component_type, arg_spec.args)
            )
        required_type = arg_spec.annotations[arg_spec.args[0]]
        return factory(dataclass_from_dict(required_type, component_config))


class ConfigurableDevice(Generic[T_COMPONENT, T_DEVICE_CONFIG, T_COMPONENT_CONFIG], AbstractDevice):
    def __init__(self,
                 device_config: T_DEVICE_CONFIG,
                 component_factory: ComponentFactory[Any, T_COMPONENT],
                 component_updater: ComponentUpdater[T_COMPONENT],
                 initializer: Callable = lambda: None,
                 error_handler: Callable = lambda: None) -> None:
        self.__initializer = initializer
        self.__error_handler = error_handler
        self.__component_factory = component_factory
        self.__component_updater = component_updater
        self.device_config = device_config
        self.components: Dict[str, T_COMPONENT] = {}
        self.error_timestamp = None
        try:
            self.__initializer()
        except Exception:
            log.exception(f"Initialisierung von Gerät {self.device_config.name} fehlgeschlagen")

    def error_handler(self) -> None:
        error_timestamp_topic = f"openWB/set/system/device/{self.device_config.id}/error_timestamp"
        if self.error_timestamp is None:
            self.error_timestamp = timecheck.create_timestamp()
            Pub().pub(error_timestamp_topic, self.error_timestamp)
            log.debug(
                f"Fehler bei Gerät {self.device_config.name} aufgetreten, Fehlerzeitstempel: {self.error_timestamp}")
        if timecheck.check_timestamp(self.error_timestamp, 60) is False:
            try:
                self.__error_handler()
            except Exception:
                log.exception(f"Fehlerbehandlung für Gerät {self.device_config.name} fehlgeschlagen")
            else:
                log.debug(f"Fehlerbehandlung für Gerät {self.device_config.name} wurde durchgeführt.")

            self.error_timestamp = None
            Pub().pub(error_timestamp_topic, self.error_timestamp)

    def add_component(self, component_config: T_COMPONENT_CONFIG) -> None:
        with SingleComponentUpdateContext(FaultState(ComponentInfo.from_component_config(component_config))):
            component = self.__component_factory(component_config)
            component.initialized = False
            self.components["component" + str(component_config.id)] = component
            component.initialize()
            component.initialized = True

    def update(self):
        initialized_components = []
        for component in self.components.values():
            if hasattr(component, "initialized") and component.initialized:
                initialized_components.append(component)
        self.__component_updater(initialized_components, self.error_handler)
