import telnetlib


def get_version_by_telnet(expected_bytearray: str, ip_address: str, port: int = 8899):
    # telnetlib ist ab Python 3.11 deprecated
    with telnetlib.Telnet(ip_address, port, 2) as client:
        answer = client.read_until(bytearray(expected_bytearray, 'utf-8'), 2)
    return answer.decode("utf-8").split("\r\n")[-1]
