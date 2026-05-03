import struct


class Endian:
    Big = "big"
    Little = "little"


class BinaryPayloadDecoder:
    def __init__(self, payload, byteorder="big", wordorder="big"):
        self._payload = payload
        self._bo = byteorder
        self._wo = wordorder
        self._ptr = 0

    @classmethod
    def fromRegisters(cls, registers, byteorder="big", wordorder="big"):
        if wordorder == "little":
            registers = list(reversed(registers))
        raw = b""
        for r in registers:
            raw += struct.pack(">H", r)
        return cls(raw, byteorder, wordorder)

    def reset(self):
        self._ptr = 0

    def skip_bytes(self, n):
        self._ptr += n

    def _decode(self, fmt):
        sz = struct.calcsize(fmt)
        data = self._payload[self._ptr:self._ptr + sz]
        self._ptr += sz
        if ">" not in fmt and "<" not in fmt:
            fmt = ">" + fmt
        return struct.unpack(fmt, data)[0]

    def decode_8bit_uint(self):
        return self._decode("B")

    def decode_16bit_uint(self):
        return self._decode(">H")

    def decode_16bit_int(self):
        return self._decode(">h")

    def decode_32bit_uint(self):
        return self._decode(">I")

    def decode_32bit_int(self):
        return self._decode(">i")

    def decode_64bit_uint(self):
        return self._decode(">Q")

    def decode_64bit_int(self):
        return self._decode(">q")

    def decode_32bit_float(self):
        return self._decode(">f")

    def decode_64bit_float(self):
        return self._decode(">d")


class BinaryPayloadBuilder:
    def __init__(self, byteorder="big", wordorder="big"):
        self._bo = byteorder
        self._wo = wordorder
        self._regs = []

    def reset(self):
        self._regs = []

    def _add(self, value, fmt):
        if ">" not in fmt and "<" not in fmt:
            fmt = ">" + fmt
        data = struct.pack(fmt, value)
        regs = []
        for i in range(0, len(data), 2):
            chunk = data[i:i+2]
            if len(chunk) == 1:
                chunk = b"\x00" + chunk
            regs.append(struct.unpack(">H", chunk)[0])
        if self._wo == "little":
            regs.reverse()
        self._regs.extend(regs)

    def add_8bit_uint(self, v):
        self._add(v, "B")

    def add_16bit_uint(self, v):
        self._add(v, ">H")

    def add_16bit_int(self, v):
        self._add(v, ">h")

    def add_32bit_uint(self, v):
        self._add(v, ">I")

    def add_32bit_int(self, v):
        self._add(v, ">i")

    def add_64bit_uint(self, v):
        self._add(v, ">Q")

    def add_64bit_int(self, v):
        self._add(v, ">q")

    def add_32bit_float(self, v):
        self._add(v, ">f")

    def add_64bit_float(self, v):
        self._add(v, ">d")

    def to_registers(self):
        return list(self._regs)
