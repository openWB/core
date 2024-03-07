import telnetlib


def get_version_by_telnet(expected_bytearray: str, ip_address: str, port: int = 8898):
    # telnetlib ist ab Python 3.11 deprecated
    with telnetlib.Telnet(ip_address, port, 2) as client:
        answer = client.read_until(bytearray(expected_bytearray, 'utf-8'), 2)
    return answer.decode("utf-8").split("\r\n")[-1]

# Telnetlib
# Verbindungen werden nicht geschlossen
# def get_or_create_eventloop() -> asyncio.AbstractEventLoop:
#     try:
#         return asyncio.get_event_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         return asyncio.get_event_loop()
# loop = get_or_create_eventloop()
# coro = telnetlib3.open_connection(self.config.configuration.ip_address, 8898, shell=self._shell)
# reader, writer = loop.run_until_complete(coro)
# loop.run_until_complete(writer.protocol.waiter_closed)
# time.sleep(2)
# writer.close()
# reader.close()

# async def _shell(self, reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):
#     for i in range(0, 3):
#         try:
#             outp = await asyncio.wait_for(reader.readline(), timeout=3)
#         except asyncio.exceptions.TimeoutError:
#             # writer.close()
#             raise FaultState.error(
#                 "Firmware des openWB satellit ist nicht mit openWB software2 kompatibel. "
#                 "Bitte den Support kontaktieren.")
#         if not outp:
#             # End of File
#             break
#         for version in self.VALID_VERSIONS:
#             if version in outp:
#                 self.version = True
#                 log.debug("Firmware des openWB satellit ist mit openWB software2 kompatibel.")
#                 return
#     else:
#         self.version = False
#         raise ValueError
