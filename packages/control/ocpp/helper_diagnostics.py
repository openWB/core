
import asyncio
import ftplib
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Dict, Optional
from urllib.parse import SplitResult, unquote, urlsplit

"""
Test Location Homeoffice
ftp://test:test@192.168.178.36:2121/uploads/test1.py

Test Location Büro
ftp://test:test@192.168.1.97:2121/uploads/test1.py
192.168.1.97
"""


def _parse_server_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=timezone.utc
    ).astimezone().replace(tzinfo=None)


# Filtert die OCPP-Logeinträge nach einem gegebenen Start- und Stoppzeitpunkt
# Wenn keine Start- oder Stoppzeit angegeben ist, werden alle Logeinträge zurückgegeben.
def filter_ocpp_log(start: Optional[str], stop: Optional[str]) -> list[str]:
    log_path = Path(__file__).resolve().parents[3] / "ramdisk" / "ocpp.log"
    with log_path.open(encoding="utf-8") as log_file:
        lines = log_file.readlines()

    start_time = _parse_server_time(start).replace(second=0, microsecond=0) if start is not None else None
    stop_time = _parse_server_time(stop).replace(second=0, microsecond=0) if stop is not None else None
    if start_time is not None and stop_time is not None and start_time > stop_time:
        raise ValueError("start muss vor oder gleich stop liegen")

    log_entries = []
    log_minutes = set()
    for line in lines:
        try:
            line_time = datetime.strptime(line.split(" - ", 1)[0], "%Y-%m-%d %H:%M:%S,%f")
        except ValueError:
            continue

        minute = line_time.replace(second=0, microsecond=0)
        log_entries.append((minute, line))
        log_minutes.add(minute)

    available_minutes = sorted(log_minutes)

    def resolve_boundary(boundary: Optional[datetime]) -> Optional[datetime]:
        if boundary is None:
            return None
        return next(
            (
                minute for minute in available_minutes
                if minute >= boundary
                and minute.date() == boundary.date()
            ),
            None,
        )

    start_time = resolve_boundary(start_time)
    stop_time = resolve_boundary(stop_time)
    if start_time is None and stop_time is None:
        # Wenn weder Start- noch Stoppzeit angegeben ist, werden alle Logeinträge zurückgegeben.
        return lines

    matching_lines = []
    for minute, line in log_entries:
        if stop_time is not None and minute > stop_time:
            break
        if start_time is not None and minute < start_time:
            continue
        matching_lines.append(line)
    return matching_lines


# Erstellt eine Diagnosedatei basierend auf den gefilterten OCPP-Logeinträgen.
# diese Datei wird dann per FTP übertragen
async def create_diagnostics(
    start_time: Optional[str] = None,
    stop_time: Optional[str] = None,
) -> str:
    log_lines = filter_ocpp_log(start_time, stop_time)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="openwb-diagnostics-",
        suffix=".txt",
        delete=False,
    ) as diagnostics_file:
        diagnostics_file.writelines(log_lines)
        return diagnostics_file.name


def _parse_ftp_location(location: str) -> SplitResult:
    parsed = urlsplit(location)
    if parsed.scheme.lower() != "ftp":
        raise ValueError(f"Nicht unterstütztes Upload-Protokoll: {parsed.scheme or '(kein Schema)'}")
    if not parsed.hostname:
        raise ValueError("FTP-Ziel enthält keinen Hostnamen")
    if not parsed.path or parsed.path == "/":
        raise ValueError("FTP-Ziel enthält keinen Dateipfad")
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
    ftp = ftplib.FTP()
    try:
        ftp.connect(location.hostname, location.port or 21, timeout=30)
        username = unquote(location.username) if location.username else "anonymous"
        if location.password is not None:
            password = unquote(location.password)
        else:
            password = "" if location.username else "anonymous@"
        ftp.login(username, password)
        ftp.set_pasv(True)
        remote_path = unquote(location.path)
        with open(file_path, "rb") as diagnostics_file:
            ftp.storbinary(f"STOR {remote_path}", diagnostics_file)
    finally:
        ftp.close()


async def _upload_ftp(file_path: str, location: str) -> None:
    parsed_location = _parse_ftp_location(location)
    await asyncio.to_thread(_upload_ftp_sync, file_path, parsed_location)


_UPLOADERS: Dict[str, Callable[[str, str], Awaitable[None]]] = {
    "ftp": _upload_ftp,
}


async def upload_diagnostics(file_path: str, location: str, retries: Optional[int] = 0, retry_interval: Optional[int] = 0):
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
