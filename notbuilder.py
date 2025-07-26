import requests
import urllib.request
from fernet import Fernet

# 1) Déchiffre le payload initial
key = b'0mKkGxyqdTZtwW24PAmNW-slDG-vSN-2n4gMoJlXZgU='
cipher = Fernet(key)
encrypted = b'…la longue chaîne…'
payload_code = cipher.decrypt(encrypted).decode('utf-8')

# 2) Define a generic interceptor
def intercept_request(*args, **kwargs):
    # args[0] devrait être l'URL
    url = args[0] if args else kwargs.get('url')
    print(f"[INTERCEPT] URL demandée : {url}")
    class DummyResp:
        text = ''          # ou stub plus complet si besoin
    return DummyResp()

# Patch dans requests
requests.get            = intercept_request
requests.post           = intercept_request
requests.request        = intercept_request
requests.Session.request= intercept_request

# Patch dans urllib
urllib.request.urlopen  = lambda req, *a, **k: intercept_request(req.get_full_url() \
                                     if hasattr(req, 'get_full_url') else req)

# 3) Exécute le premier payload
exec(payload_code)
