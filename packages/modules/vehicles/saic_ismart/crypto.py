#!/usr/bin/env python3
"""Krypto-Bausteine für die SAIC/MG-iSMART-Cloud-API.

Protokoll (Request-/Response-Verschlüsselung, Signatur) reverse-engineered von
https://github.com/SAIC-iSmart-API/saic-python-client-ng (MIT), das selbst asyncio/httpx
nutzt und daher Python 3.11+ braucht (openWB läuft auf 3.9) - hier synchron mit Standard-
AES-CBC (über die in openWB bereits vorhandene `cryptography`-Bibliothek) nachgebaut.

Jeder Request-/Response-Body wird AES-128-CBC-verschlüsselt (Schlüssel/IV aus Pfad,
Tenant-ID, Nutzer-Token und Zeitstempel per MD5 abgeleitet) und zusätzlich mit einer
HMAC-SHA256-Signatur (APP-VERIFICATION-STRING-Header) versehen.
"""
import hashlib
import hmac


def md5_hex(content: str, pad: bool = False) -> str:
    if pad:
        content = content + "00"
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def sha1_hex(content: str) -> str:
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


def sha256_hex(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def aes_encrypt_hex(plaintext: str, key_hex: str, iv_hex: str) -> str:
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    key = bytes.fromhex(key_hex)
    iv = bytes.fromhex(iv_hex)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return (encryptor.update(padded) + encryptor.finalize()).hex()


def aes_decrypt_hex(cipher_hex: str, key_hex: str, iv_hex: str) -> str:
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    key = bytes.fromhex(key_hex)
    iv = bytes.fromhex(iv_hex)
    ct = bytes.fromhex(cipher_hex)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")


def _body_key_iv(request_path: str, tenant_id: str, user_token: str, timestamp_ms: str,
                 content_type: str) -> tuple:
    key = md5_hex(md5_hex(request_path + tenant_id + user_token + "app") +
                  timestamp_ms + "1" + content_type)
    iv = md5_hex(timestamp_ms)
    return key, iv


def app_verification_string(request_path: str, timestamp_ms: str, tenant_id: str,
                            content_type: str, request_content: str, user_token: str) -> str:
    """HMAC-SHA256-Signatur über Pfad/Tenant/Token/Zeitstempel/verschlüsselten Body,
    wie vom Server unter dem Header APP-VERIFICATION-STRING erwartet."""
    key, iv = _body_key_iv(request_path, tenant_id, user_token, timestamp_ms, content_type)
    encrypted_content = aes_encrypt_hex(request_content, key, iv) if request_content else ""
    message = (request_path + tenant_id + user_token + "app" + timestamp_ms + "1" +
               content_type + encrypted_content)
    hmac_key = md5_hex(key + timestamp_ms)
    return hmac.new(hmac_key.encode("utf-8"), msg=message.encode("utf-8"),
                    digestmod=hashlib.sha256).hexdigest()


def encrypt_request_body(request_path: str, tenant_id: str, user_token: str,
                         timestamp_ms: str, content_type: str, plaintext_body: str) -> str:
    if not plaintext_body:
        return plaintext_body
    key, iv = _body_key_iv(request_path, tenant_id, user_token, timestamp_ms, content_type)
    return aes_encrypt_hex(plaintext_body, key, iv)


def decrypt_response_body(cipher_hex: str, timestamp_ms: str, content_type: str) -> str:
    key = md5_hex(timestamp_ms + "1" + content_type)
    iv = md5_hex(timestamp_ms)
    return aes_decrypt_hex(cipher_hex, key, iv)


def build_signed_headers(request_path: str, tenant_id: str, user_token: str, region: str,
                         content_type: str, encrypted_body: str, plaintext_body: str,
                         timestamp_ms: str) -> dict:
    headers = {
        "User-Agent": "Europe/2.1.0 (iPad; iOS 18.5; Scale/2.00)",
        "Content-Type": f"{content_type};charset=utf-8",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "REGION": region,
        "APP-SEND-DATE": timestamp_ms,
        "APP-CONTENT-ENCRYPTED": "1",
        "tenant-id": tenant_id,
        "User-Type": "app",
        "APP-LANGUAGE-TYPE": "en",
        "ORIGINAL-CONTENT-TYPE": content_type,
    }
    if user_token:
        headers["blade-auth"] = user_token
    headers["APP-VERIFICATION-STRING"] = app_verification_string(
        request_path, timestamp_ms, tenant_id, content_type, plaintext_body, user_token)
    return headers


def pwd_login_hash(password: str) -> str:
    return sha1_hex(password)


def vin_hash(vin: str) -> str:
    return sha256_hex(vin)
