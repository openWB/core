import socket

try:
    from telnetlib3 import telnetlib
except ModuleNotFoundError as error:
    if error.name != "telnetlib3":
        raise
    import telnetlib


def get_version_by_telnet(expected_bytearray: str, ip_address: str, port: int = 8898):
    if ip_address is None:
        # None liefert einen ValueError genauso wie wenn telnet nicht aktiv ist.
        raise socket.timeout("Die IP-Adresse ist nicht erreichbar. Bitte überprüfe die Einstellungen.")
    with telnetlib.Telnet(ip_address, port, 2) as client:
        answer = client.read_until(bytearray(expected_bytearray, 'utf-8'), 2)
    return answer.decode("utf-8").split("\r\n")[-1]
