
import asyncio
import ftplib
import posixpath
import ssl
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable, Dict, Optional
from urllib.parse import SplitResult, unquote, urlsplit


def _parse_server_time(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("OCPP dateTime muss eine Zeitzone enthalten")

    # Das openWB-Log verwendet lokale, naive Zeitstempel.
    return parsed.astimezone().replace(tzinfo=None)


# Filtert die OCPP-Logeinträge einer Chargebox nach einem gegebenen Start- und Stoppzeitpunkt.
# Ohne Zeitgrenzen werden alle Logeinträge dieser Chargebox zurückgegeben.
def filter_ocpp_log(chargebox_id: str, start: Optional[str], stop: Optional[str]) -> list[str]:
    log_path = Path(__file__).resolve().parents[3] / "ramdisk" / "ocpp.log"
    with log_path.open(encoding="utf-8") as log_file:
        lines = log_file.readlines()

    start_time = _parse_server_time(start) if start is not None else None
    stop_time = _parse_server_time(stop) if stop is not None else None
    if start_time is not None and stop_time is not None and start_time > stop_time:
        raise ValueError("start muss vor oder gleich stop liegen")

    matching_lines = []
    for line in lines:
        log_fields = line.split(" - ", 3)
        if len(log_fields) != 4:
            continue
        context_field = log_fields[2]
        if not context_field.startswith("{") or not context_field.endswith("}"):
            continue
        _, separator, logged_chargebox_id = context_field[1:-1].partition(":")
        if not separator or logged_chargebox_id != chargebox_id:
            continue

        if start_time is not None or stop_time is not None:
            try:
                line_time = datetime.strptime(log_fields[0], "%Y-%m-%d %H:%M:%S,%f")
            except ValueError:
                continue

            if start_time is not None and line_time < start_time:
                continue
            if stop_time is not None and line_time > stop_time:
                continue
        matching_lines.append(line)
    return matching_lines


# Erstellt eine Diagnosedatei basierend auf den gefilterten OCPP-Logeinträgen.
# diese Datei wird dann per FTP oder FTPS übertragen
def _create_diagnostics_sync(
    chargebox_id: str,
    start_time: Optional[str] = None,
    stop_time: Optional[str] = None,
) -> str:
    log_lines = filter_ocpp_log(chargebox_id, start_time, stop_time,)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="openwb-diagnostics-",
        suffix=".log",
        delete=False,
    ) as diagnostics_file:
        diagnostics_file.writelines(log_lines)
        return diagnostics_file.name


# Auslagerung in einen eigenen Thread,
# damit der OCPP-Event-Loop nicht blockiert wird.
async def create_diagnostics(
    chargebox_id: str,
    start_time: Optional[str] = None,
    stop_time: Optional[str] = None,
) -> str:
    return await asyncio.to_thread(_create_diagnostics_sync, chargebox_id, start_time, stop_time)


def _parse_ftp_location(location: str) -> SplitResult:
    parsed = urlsplit(location)
    if parsed.scheme.lower() not in ("ftp", "ftps"):
        raise ValueError(f"Nicht unterstütztes Upload-Protokoll: {parsed.scheme or '(kein Schema)'}")
    if not parsed.hostname:
        raise ValueError("FTP-Ziel enthält keinen Hostnamen")
    if not parsed.path:
        raise ValueError("FTP-Ziel enthält kein Zielverzeichnis")
    if parsed.query or parsed.fragment:
        raise ValueError("FTP-Ziel darf keine Query oder Fragment enthalten")
    try:
        parsed.port
    except ValueError as error:
        raise ValueError("Ungültiger FTP-Port") from error
    decoded_fields = (
        unquote(parsed.path),
        unquote(parsed.username or ""),
        unquote(parsed.password or ""),
    )
    if any(character in field for field in decoded_fields for character in "\r\n"):
        raise ValueError("FTP-Ziel enthält ungültige Steuerzeichen")
    return parsed


def _upload_ftp_sync(file_path: str, location: SplitResult) -> None:
    use_tls = location.scheme.lower() == "ftps"
    # Zum testen
    # ftp = (ftplib.FTP_TLS(context=ssl.create_default_context(cafile="/var/www/html/openWB/server.crt"))
    ftp = (ftplib.FTP_TLS(context=ssl.create_default_context())
           if use_tls else ftplib.FTP())
    try:
        ftp.connect(location.hostname, location.port or 21, timeout=30)
        username = unquote(location.username) if location.username else "anonymous"
        if location.password is not None:
            password = unquote(location.password)
        else:
            password = "" if location.username else "anonymous@"
        ftp.login(username, password)
        if use_tls:
            ftp.prot_p()
        ftp.set_pasv(True)
        remote_directory = unquote(location.path)
        remote_path = posixpath.join(
            remote_directory.rstrip("/") or "/",
            Path(file_path).name,
        )
        with open(file_path, "rb") as diagnostics_file:
            ftp.storbinary(f"STOR {remote_path}", diagnostics_file)
    finally:
        ftp.close()


async def _upload_ftp(file_path: str, location: str) -> None:
    parsed_location = _parse_ftp_location(location)
    await asyncio.to_thread(_upload_ftp_sync, file_path, parsed_location)


_UPLOADERS: Dict[str, Callable[[str, str], Awaitable[None]]] = {
    "ftp": _upload_ftp,
    "ftps": _upload_ftp,
}


async def upload_diagnostics(file_path: str,
                             location: str,
                             retries: Optional[int] = 0,
                             retry_interval: Optional[int] = 0):
    scheme = urlsplit(location).scheme.lower()
    uploader = _UPLOADERS.get(scheme)
    if uploader is None:
        raise ValueError(f"Nicht unterstütztes Upload-Protokoll: {scheme or '(kein Schema)'}")

    retry_count = max(0, retries or 0)
    interval = max(0, retry_interval or 0)

    for attempt in range(retry_count + 1):
        try:
            await uploader(file_path, location)
            return
        except Exception:
            if attempt == retry_count:
                raise
            await asyncio.sleep(interval)
