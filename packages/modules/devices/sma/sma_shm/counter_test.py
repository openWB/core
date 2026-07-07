import base64

from modules.common.component_state import CounterState
from modules.devices.sma.sma_shm import counter, speedwiredecoder

# This sample was collected from an SMA Energy Meter with Firmware 2.0.18.R on 2021-12-22:
SAMPLE_SMA_ENERGY_EM = """
U01BAAAEAqAAAAABAkQAEGBpAV1xVXzY4imVNQABBAAAAAAAAAEIAAAAAAZJYH0AAAIEAAAB03YAA
ggAAAAASKlcgTAAAwQAAAAOpgADCAAAAAABs7fAAAAEBAAAAAAAAAQIAAAAAAHA7tMwAAkEAAAAAA
AACQgAAAAABtNNHmAACgQAAAHTsgAKCAAAAABIyAd/4AANBAAAAAPoABUEAAAAAAAAFQgAAAAAAcc
tgCAAFgQAAACfQgAWCAAAAAAYndxeAAAXBAAAAAaQABcIAAAAAAB1R9JwABgEAAAAAAAAGAgAAAAA
AMHoL4AAHQQAAAAAAAAdCAAAAAACC2mY8AAeBAAAAJ9gAB4IAAAAABinDvUAAB8EAAAAQwgAIAQAA
AOjZgAhBAAAAAPnACkEAAAAAAAAKQgAAAAAAiAQN/AAKgQAAACfQgAqCAAAAAAYhLpHcAArBAAAAA
cIACsIAAAAAAFF1ESgACwEAAAAAAAALAgAAAAAADY1tcAAMQQAAAAAAAAxCAAAAAACUKu34AAyBAA
AAJ9+ADIIAAAAABibCGxQADMEAAAAQswANAQAAAOmwgA1BAAAAAPnAD0EAAAAAAAAPQgAAAAAAqNm
AhAAPgQAAACU8gA+CAAAAAAXyAkY4AA/BAAAAAEOAD8IAAAAAAB26GxwAEAEAAAAAAAAQAgAAAAAA
Ucd26AARQQAAAAAAABFCAAAAAADCmzGsABGBAAAAJTyAEYIAAAAABfUThagAEcEAAAAPpQASAQAAA
OkkgBJBAAAAAPokAAAAAIAElIAAAAA
"""


def test_process_datagram_energy_meter():
    # setup
    data = base64.b64decode(SAMPLE_SMA_ENERGY_EM)
    sma_data = speedwiredecoder.decode_speedwire(data)
    sma_counter = counter.create_component(counter.component_descriptor.configuration_factory())
    sma_counter.initialize()

    # execution
    sma_counter.read_datagram(sma_data)

    # evaluation
    assert vars(sma_counter.store.delegate.delegate.state) == vars(CounterState(currents=[-17.16, -17.1, -16.02],
                                                                                powers=[-4077.0, -4077.0, -3813.0],
                                                                                voltages=[238.438, 239.298, 238.738],
                                                                                power_factors=[0.999, 0.999, 1.0],
                                                                                imported=7500240.0,
                                                                                exported=86688627.0,
                                                                                power=-11967.0,
                                                                                frequency=50,
                                                                                serial_number=None))
