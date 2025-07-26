import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

url = 'https://totohateinenkleinencock.ru/paste?re…o=W4SP-Stealer'

# 1) Lance Chrome “indétectable”
options = uc.ChromeOptions()
options.headless = True
options.add_argument('--disable-blink-features=AutomationControlled')
driver = uc.Chrome(options=options)

try:
    # 2) Récupère la page (attend que le JS challenge soit résolu)
    driver.get(url)
    # 3) Recherche la balise <pre> contenant le code
    pre = driver.find_element(By.TAG_NAME, 'pre')
    raw = pre.text

    # 4) Écrit dans un fichier local, sans jamais exécuter le contenu
    with open('payload_w4sp.py', 'w', encoding='utf-8') as f:
        f.write(raw)

    print("✅ Code sauvegardé dans payload_w4sp.py — tu peux maintenant l'analyser à froid.")
finally:
    driver.quit()
