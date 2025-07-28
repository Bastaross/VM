# extract_chromium_passwords_corrected.py

import os
import json
import base64
import sqlite3
import shutil
import tempfile
from Crypto.Cipher import AES
import win32crypt

# Define browsers and profiles to search
USERPROFILE = os.getenv('USERPROFILE')
LOCALAPPDATA = os.getenv('LOCALAPPDATA')
APPDATA = os.getenv('APPDATA')

CHROMIUM_BROWSERS = [
    {"name": "Google Chrome", "path": os.path.join(LOCALAPPDATA, "Google", "Chrome", "User Data")},
    {"name": "Microsoft Edge", "path": os.path.join(LOCALAPPDATA, "Microsoft", "Edge", "User Data")},
    {"name": "Opera", "path": os.path.join(APPDATA, "Opera Software", "Opera Stable")},
    {"name": "Brave", "path": os.path.join(LOCALAPPDATA, "BraveSoftware", "Brave-Browser", "User Data")},
    {"name": "Yandex", "path": os.path.join(APPDATA, "Yandex", "YandexBrowser", "User Data")},
]

CHROMIUM_PROFILES = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]

def get_decryption_key(local_state_path):
    """Retrieve AES key from Local State using Windows DPAPI."""
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
    encrypted_key = base64.b64decode(encrypted_key_b64)[5:]  # strip 'DPAPI' prefix
    _, key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)
    return key

def decrypt_password(buff, key):
    """
    Decrypt a Chrome encrypted password blob.
    Supports AES-GCM (prefix 'v10') and DPAPI fallback.
    """
    try:
        if buff.startswith(b'v10'):
            iv = buff[3:3+12]
            ciphertext = buff[3+12:-16]
            tag = buff[-16:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted.decode('utf-8', errors='ignore')
    except Exception:
        pass
    try:
        # DPAPI fallback
        _, decrypted = win32crypt.CryptUnprotectData(buff, None, None, None, 0)
        return decrypted.decode('utf-8', errors='ignore')
    except Exception:
        return ""

def extract_passwords():
    results = []
    for browser in CHROMIUM_BROWSERS:
        base_path = browser["path"]
        if not os.path.isdir(base_path):
            continue
        local_state = os.path.join(base_path, "Local State")
        if not os.path.isfile(local_state):
            continue
        key = get_decryption_key(local_state)
        for profile in CHROMIUM_PROFILES:
            login_db = os.path.join(base_path, profile, "Login Data")
            if not os.path.isfile(login_db):
                continue
            # Copy DB to a temporary file
            fd, tmp_path = tempfile.mkstemp(suffix=".db")
            os.close(fd)
            shutil.copy2(login_db, tmp_path)
            try:
                conn = sqlite3.connect(tmp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                for origin_url, username, encrypted_value in cursor.fetchall():
                    if not username and not encrypted_value:
                        continue
                    # Ensure it's bytes
                    blob = encrypted_value if isinstance(encrypted_value, (bytes, bytearray)) else bytes(encrypted_value)
                    password = decrypt_password(blob, key)
                    results.append({
                        "browser": browser["name"],
                        "profile": profile,
                        "url": origin_url,
                        "username": username,
                        "password": password
                    })
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Erreur lecture de la DB temporaire {tmp_path}: {e}")
            finally:
                os.remove(tmp_path)
    return results

def main():
    pw_list = extract_passwords()
    if not pw_list:
        print("Aucun mot de passe trouvé.")
    else:
        print("\n=== Mots de passe extraits corrigés ===\n")
        for entry in pw_list:
            print(f"Navigateur: {entry['browser']} / Profil: {entry['profile']}")
            print(f"URL:         {entry['url']}")
            print(f"Utilisateur: {entry['username']}")
            print(f"Mot de passe: {entry['password']}\n")

if __name__ == "__main__":
    main()


