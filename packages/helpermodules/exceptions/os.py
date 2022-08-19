from helpermodules.exceptions.registry import ExceptionRegistry


def handle_os_error(e: OSError):
    code = e.errno
    if code == 113:
        return "Die Verbindung zum Host ist fehlgeschlagen. Überprüfe Adresse und Netzwerk."
    return "OSError {}: Unbekannter Fehler {}".format(code, e.strerror)


def register_os_exception_handlers(registry: ExceptionRegistry) -> None:
    registry.add(OSError, handle_os_error)
