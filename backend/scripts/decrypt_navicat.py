# -*- coding: utf-8 -*-
"""Decrypt Navicat 16 (V3) saved password for the HRProject server.

Reads HKCU:\\Software\\PremiumSoft\\Navicat\\Servers\\HRProject\\Pwd_2 and the
Windows Credential Manager 'navicat_cred' blob, derives the AES-256-GCM key and
decrypts the password. The plaintext password is NEVER printed; it is written
to scripts/.pwd_secret (gitignored temp file) for in-process use by follow-up
scripts.
"""
import ctypes
import struct
import winreg
from ctypes import wintypes
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import GCM

SECRET_OUT = Path(__file__).with_name(".pwd_secret")


class CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", wintypes.LPVOID),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


PCREDENTIALW = ctypes.POINTER(CREDENTIALW)
advapi32 = ctypes.windll.advapi32
advapi32.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(PCREDENTIALW)]
advapi32.CredReadW.restype = wintypes.BOOL
advapi32.CredFree.argtypes = [wintypes.LPVOID]
CRED_TYPE_GENERIC = 1


def fetch_navicat_cred() -> bytes:
    pcred = PCREDENTIALW()
    if not advapi32.CredReadW("navicat_cred", CRED_TYPE_GENERIC, 0, ctypes.byref(pcred)):
        raise RuntimeError("CredReadW failed for 'navicat_cred'")
    try:
        size = pcred.contents.CredentialBlobSize
        blob = ctypes.string_at(pcred.contents.CredentialBlob, size)
        for enc in ("ascii", "utf-16-le"):
            try:
                return bytes.fromhex(blob.decode(enc))
            except (ValueError, UnicodeDecodeError):
                continue
        # fall back: treat blob as raw key bytes
        return blob
    finally:
        advapi32.CredFree(pcred)


def derive_v3_key(data: bytes) -> bytes:
    table = bytes(i + 1 for i in range(32))
    key = bytearray(data)
    key[25:29] = [table[i] for i in (2, 0, 2, 5)]
    return bytes(key)


def unpad_v3(data: bytes) -> bytes:
    blocksize = 16
    content_length, = struct.unpack("<H", data[:2])
    total = ((2 + content_length + blocksize - 1) // blocksize) * blocksize
    padding_length = total - (2 + content_length)
    return data[2:2 + content_length]


def decrypt_v3(hex_str: str, key: bytes) -> str:
    data = bytes.fromhex(hex_str)
    nonce = data[:12]
    tag = data[-16:]
    ciphertext = data[12:-16]
    cipher = Cipher(AES(key), GCM(nonce, tag))
    dec = cipher.decryptor()
    padded = dec.update(ciphertext) + dec.finalize()
    return unpad_v3(padded).decode("utf-8")


def main() -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Software\PremiumSoft\Navicat\Servers\HRProject") as k:
        pwd2, _ = winreg.QueryValueEx(k, "Pwd_2")
    cred = fetch_navicat_cred()
    key = derive_v3_key(cred)
    password = decrypt_v3(pwd2, key)
    SECRET_OUT.write_text(password, encoding="utf-8")
    print("OK: decrypted password length =", len(password))


if __name__ == "__main__":
    main()
