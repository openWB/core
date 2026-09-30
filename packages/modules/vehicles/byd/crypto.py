#!/usr/bin/env python3
"""Krypto-Bausteine für die BYD-Cloud-API.

Synchron und ohne Fremdbibliotheken (außer `cryptography`, die in openWB
bereits vorhanden ist) nach Python 3.9 portiert. Der Bangcle-Whitebox-AES-Teil
(Tabellen-Lookup statt normalem AES-Key-Schedule, wie es die offizielle BYD-App
als App-Hardening nutzt) sowie die Ableitung der Login-/Sitzungs-Keys stammen
aus dem MIT-lizenzierten Projekt https://github.com/jkaberg/pyBYD, das dieses
Schema aus der BYD-App reverse-engineered hat. Die Tabellen-Binärdatei
(bangcle_tables.bin) wurde von dort unverändert übernommen.

Zwei unabhängige Verschlüsselungs-Layer:
  1. Bangcle (Whitebox-AES-CBC, Zero-IV): verschlüsselt das komplette äußere
     JSON-Envelope für den Transport ({"request": "<Bangcle-Text>"}).
  2. Standard-AES-128-CBC (Zero-IV): verschlüsselt/entschlüsselt innerhalb des
     Envelopes die Felder "encryData" (Request) bzw. "respondData" (Response).
     Der Schlüssel dafür wird beim Login aus dem Passwort abgeleitet, danach
     aus dem vom Server erhaltenen encryToken (siehe session_keys()).
"""
import hashlib
import json
import struct
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional

_ZERO_IV = b"\x00" * 16
_TABLES_FILE = Path(__file__).parent / "bangcle_tables.bin"

# --- Binärformat der Tabellendatei (siehe pyBYD._crypto.bangcle) ---
_MAGIC = b"BGTB"
_VERSION = 1
_TABLE_COUNT = 8
_HEADER_SIZE = 8
_INDEX_ENTRY_SIZE = 8
_TABLE_SPECS = [
    ("inv_round", 0x28000), ("inv_xor", 0x3C000), ("inv_first", 0x1000),
    ("round", 0x28000), ("xor", 0x3C000), ("final", 0x1000),
    ("perm_decrypt", 8), ("perm_encrypt", 8),
]


class BydCryptoError(Exception):
    """Fehler beim Ver-/Entschlüsseln oder beim Laden der Bangcle-Tabellen."""


class BangcleTables(NamedTuple):
    inv_round: bytes
    inv_xor: bytes
    inv_first: bytes
    round: bytes
    xor: bytes
    final: bytes
    perm_decrypt: bytes
    perm_encrypt: bytes


_tables_cache: Optional[BangcleTables] = None


def _load_tables() -> BangcleTables:
    global _tables_cache
    if _tables_cache is not None:
        return _tables_cache
    try:
        data = _TABLES_FILE.read_bytes()
    except FileNotFoundError as exc:
        raise BydCryptoError(f"bangcle_tables.bin nicht gefunden unter {_TABLES_FILE}") from exc

    if data[:4] != _MAGIC or len(data) < _HEADER_SIZE + _TABLE_COUNT * _INDEX_ENTRY_SIZE:
        raise BydCryptoError("bangcle_tables.bin ist beschädigt oder hat ein unbekanntes Format")

    tables = []
    for i, (name, expected_len) in enumerate(_TABLE_SPECS):
        idx_off = _HEADER_SIZE + i * _INDEX_ENTRY_SIZE
        offset, length = struct.unpack_from("<II", data, idx_off)
        if length != expected_len:
            raise BydCryptoError(f"Tabelle {name}: erwartet {expected_len} Bytes, bekommen {length}")
        tables.append(data[offset:offset + length])

    _tables_cache = BangcleTables(*tables)
    return _tables_cache


def _prepare_matrix(block: bytes, out: bytearray) -> None:
    for col in range(4):
        for row in range(4):
            out[col * 8 + row] = block[col + row * 4]


def _decrypt_block(tables: BangcleTables, block: bytes) -> bytes:
    state = bytearray(32)
    temp64 = bytearray(64)
    output = bytearray(16)
    _prepare_matrix(block, state)

    for rnd in range(9, 0, -1):
        l21 = rnd * 4
        perm_ptr = 0
        for i in range(4):
            perm = tables.perm_decrypt[perm_ptr]
            base = i * 16
            for j in range(4):
                u = (perm + j) & 3
                byte_val = state[i * 8 + u]
                idx = byte_val + (i + (l21 + u) * 4) * 256
                value = struct.unpack_from("<I", tables.inv_round, idx * 4)[0]
                struct.pack_into("<I", temp64, base + j * 4, value)
            perm_ptr += 2

        i15 = 1
        for l21x in range(4):
            off = l21x
            for l9x in range(4):
                v0 = temp64[off]
                u6 = v0 & 0xF
                u26 = v0 & 0xF0
                f0, f1, f2 = temp64[off + 0x10], temp64[off + 0x20], temp64[off + 0x30]
                l2 = l9x * 0x18 + rnd * 0x60
                i25 = i15
                for l16 in range(3):
                    bv = f0 if l16 == 0 else (f1 if l16 == 1 else f2)
                    u1 = (bv << 4) & 0xFF
                    u27 = u6 | u1
                    u26 = ((u26 >> 4) | ((bv >> 4) << 4)) & 0xFF
                    idx1 = (l2 + (i25 - 1)) * 0x100 + u27
                    u6 = tables.inv_xor[idx1] & 0xF
                    idx2 = (l2 + i25) * 0x100 + u26
                    bnew = tables.inv_xor[idx2]
                    u26 = (bnew & 0xF) << 4
                    i25 += 2
                state[l9x + l21x * 8] = (u26 | u6) & 0xFF
                off += 4
            i15 += 6

    tmp32 = bytearray(state)
    u8, u10, u12 = 1, 3, 2
    for row in range(4):
        state[row] = tables.inv_first[tmp32[row] + row * 0x400]
        r1 = u10 & 3
        state[8 + row] = tables.inv_first[tmp32[8 + r1] + r1 * 0x400 + 0x100]
        r2 = u12 & 3
        state[0x10 + row] = tables.inv_first[tmp32[0x10 + r2] + r2 * 0x400 + 0x200]
        r3 = u8 & 3
        state[0x18 + row] = tables.inv_first[tmp32[0x18 + r3] + r3 * 0x400 + 0x300]
        u8 += 1
        u10 += 1
        u12 += 1

    for col in range(4):
        for row in range(4):
            output[col + row * 4] = state[col * 8 + row]
    return bytes(output)


def _encrypt_block(tables: BangcleTables, block: bytes) -> bytes:
    state = bytearray(32)
    temp64 = bytearray(64)
    output = bytearray(16)
    _prepare_matrix(block, state)

    for rnd in range(9):
        l21 = rnd * 4
        perm_ptr = 0
        for i in range(4):
            perm = tables.perm_encrypt[perm_ptr]
            base = i * 16
            for j in range(4):
                u = (perm + j) & 3
                byte_val = state[i * 8 + u]
                idx = byte_val + (i + (l21 + u) * 4) * 256
                value = struct.unpack_from("<I", tables.round, idx * 4)[0]
                struct.pack_into("<I", temp64, base + j * 4, value)
            perm_ptr += 2

        i16 = 1
        for l22 in range(4):
            off = l22
            for l10 in range(4):
                v0 = temp64[off]
                u7 = v0 & 0xF
                u26 = v0 & 0xF0
                f0, f1, f2 = temp64[off + 0x10], temp64[off + 0x20], temp64[off + 0x30]
                l2 = l10 * 0x18 + rnd * 0x60
                i25 = i16
                for l17 in range(3):
                    bv = f0 if l17 == 0 else (f1 if l17 == 1 else f2)
                    u1 = (bv << 4) & 0xFF
                    u27 = u7 | u1
                    u26 = ((u26 >> 4) | ((bv >> 4) << 4)) & 0xFF
                    idx1 = (l2 + (i25 - 1)) * 0x100 + u27
                    u7 = tables.xor[idx1] & 0xF
                    idx2 = (l2 + i25) * 0x100 + u26
                    bnew = tables.xor[idx2]
                    u26 = (bnew & 0xF) << 4
                    i25 += 2
                state[l10 + l22 * 8] = (u26 | u7) & 0xFF
                off += 4
            i16 += 6

    tmp32 = bytearray(state)
    u13, u9, u11, u8e = 3, 2, 1, 0
    for row in range(4):
        r0 = (u8e + row) & 3
        state[row] = tables.final[tmp32[r0] + r0 * 0x400]
        r1 = (u11 + row) & 3
        state[8 + row] = tables.final[tmp32[8 + r1] + r1 * 0x400 + 0x100]
        r2 = (u9 + row) & 3
        state[0x10 + row] = tables.final[tmp32[0x10 + r2] + r2 * 0x400 + 0x200]
        r3 = (u13 + row) & 3
        state[0x18 + row] = tables.final[tmp32[0x18 + r3] + r3 * 0x400 + 0x300]

    for col in range(4):
        for row in range(4):
            output[col + row * 4] = state[col * 8 + row]
    return bytes(output)


def _add_pkcs7(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def _strip_pkcs7(data: bytes) -> bytes:
    if not data:
        return data
    pad = data[-1]
    if 0 < pad <= 16 and len(data) >= pad and all(b == pad for b in data[-pad:]):
        return data[:-pad]
    return data


def bangcle_encode(plaintext: str) -> str:
    """Verschlüsselt den äußeren Envelope für den Transport ('F' + base64)."""
    import base64
    tables = _load_tables()
    padded = _add_pkcs7(plaintext.encode("utf-8"))
    prev = bytearray(_ZERO_IV)
    out = bytearray(len(padded))
    for off in range(0, len(padded), 16):
        block = bytearray(padded[off:off + 16])
        for i in range(16):
            block[i] ^= prev[i]
        enc = _encrypt_block(tables, bytes(block))
        out[off:off + 16] = enc
        prev[:] = enc
    return "F" + base64.b64encode(bytes(out)).decode("ascii")


def bangcle_decode(envelope: str) -> bytes:
    """Entschlüsselt eine Bangcle-Antwort zurück zu den rohen Bytes."""
    import base64
    tables = _load_tables()
    cleaned = envelope.strip().replace("-", "+").replace("_", "/")
    if cleaned.startswith("F"):
        cleaned = cleaned[1:]
    cleaned += "=" * (-len(cleaned) % 4)
    ciphertext = base64.b64decode(cleaned)
    if not ciphertext or len(ciphertext) % 16 != 0:
        raise BydCryptoError(f"Bangcle-Ciphertext hat ungültige Länge {len(ciphertext)}")

    prev = bytearray(_ZERO_IV)
    out = bytearray(len(ciphertext))
    for off in range(0, len(ciphertext), 16):
        block = ciphertext[off:off + 16]
        dec = bytearray(_decrypt_block(tables, block))
        for i in range(16):
            dec[i] ^= prev[i]
        out[off:off + 16] = dec
        prev[:] = block
    return _strip_pkcs7(bytes(out))


# --- Standard-AES-128-CBC (Zero-IV) für encryData/respondData ---

def aes_encrypt_hex(plaintext: str, key_hex: str) -> str:
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    key = bytes.fromhex(key_hex)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(_ZERO_IV)).encryptor()
    return (encryptor.update(padded) + encryptor.finalize()).hex().upper()


def aes_decrypt_utf8(cipher_hex: str, key_hex: str) -> str:
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    key = bytes.fromhex(key_hex)
    ct = bytes.fromhex(cipher_hex)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(_ZERO_IV)).decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")


# --- Hashing / Signing ---

def md5_hex(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest().upper()


def pwd_login_key(password: str) -> str:
    """Login-AES-Key wird aus dem doppelt-MD5-gehashten Passwort abgeleitet."""
    return md5_hex(md5_hex(password))


def sha1_mixed(value: str) -> str:
    """SHA1 mit alternierender Groß-/Kleinschreibung + Entfernen führender Nullen
    an geraden Positionen (Eigenheit des BYD-Signaturschemas)."""
    digest = hashlib.sha1(value.encode("utf-8")).digest()
    mixed = "".join(
        f"{b:02x}".upper() if i % 2 == 0 else f"{b:02x}"
        for i, b in enumerate(digest)
    )
    return "".join(ch for j, ch in enumerate(mixed) if not (ch == "0" and j % 2 == 0))


def build_sign_string(fields: Dict[str, str], password_or_key: str) -> str:
    keys = sorted(fields.keys())
    joined = "&".join(f"{k}={'null' if fields[k] is None else fields[k]}" for k in keys)
    return f"{joined}&password={password_or_key}"


def compute_checkcode(payload: Dict[str, Any]) -> str:
    json_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    md5 = hashlib.md5(json_str.encode("utf-8")).hexdigest()
    return md5[24:32] + md5[8:16] + md5[16:24] + md5[0:8]


def session_keys(sign_token: str, encry_token: str) -> Dict[str, str]:
    """Leitet die beiden Sitzungs-Keys aus den beim Login erhaltenen Tokens ab."""
    return {"sign_key": md5_hex(sign_token), "content_key": md5_hex(encry_token)}
