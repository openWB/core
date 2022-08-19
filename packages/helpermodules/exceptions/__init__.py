from helpermodules.exceptions import os, registry, requests

_DEFAULT_EXCEPTION_REGISTRY = registry.ExceptionRegistry()
requests.register_request_exception_handlers(_DEFAULT_EXCEPTION_REGISTRY)
os.register_os_exception_handlers(_DEFAULT_EXCEPTION_REGISTRY)


def get_default_exception_registry() -> registry.ExceptionRegistry:
    return _DEFAULT_EXCEPTION_REGISTRY
