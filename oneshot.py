# 1) Installe cloudscraper si ce n'est pas déjà fait :
#    pip install cloudscraper

import cloudscraper

# 2) L’URL exacte du paste malveillant
url = 'https://totohateinenkleinencock.ru/paste?re…o=W4SP-Stealer'

# 3) Crée un client qui résout le challenge Cloudflare
scraper = cloudscraper.create_scraper()

# 4) Envoie la requête et récupère le texte
resp = scraper.get(url, timeout=60)
html = resp.text

# 5) Nettoie les balises <pre> si présentes
code = html.replace('<pre>', '').replace('</pre>', '')

# 6) Sauvegarde dans un fichier, sans jamais faire exec()
with open('w4sp_payload.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Contenu récupéré et sauvegardé dans w4sp_payload.py")
