import requests

url = 'https://totohateinenkleinencock.ru/paste?re…o=W4SP-Stealer'

# 1) Définition de l’User‑Agent
headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36'
    )
}

# 2) Si vous passez par Tor ou un proxy SOCKS5
proxies = {
    'http':  'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

# 3) Exécution de la requête avec headers ET proxies
r = requests.get(url, headers=headers, proxies=proxies)

# 4) Nettoyage et affichage
code = r.text.replace('<pre>', '').replace('</pre>', '')
print(code)
