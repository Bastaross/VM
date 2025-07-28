# -*- coding: utf-8 -*-
import os
import json
import base64
import sqlite3
import shutil
from pathlib import Path
import subprocess
import time

import sys
sys.stdout.reconfigure(encoding='utf-8')   # Pour afficher correctement les emojis

# IMPORTANT : Ce script est uniquement pour vérifier VOS PROPRES mots de passe
# Ne l'utilisez que sur VOTRE ordinateur personnel

try:
    import win32crypt
    from Crypto.Cipher import AES
except ImportError:
    print("Installation des dépendances nécessaires...")
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pycryptodome", "pywin32"])
    import win32crypt
    from Crypto.Cipher import AES

def kill_chrome():
    """Ferme tous les processus Chrome"""
    print("Fermeture de Chrome...")
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], 
                  stdout=subprocess.DEVNULL, 
                  stderr=subprocess.DEVNULL)
    time.sleep(2)  # Attendre que Chrome se ferme

def decrypt_password(password, key):
    """Déchiffre un mot de passe Chrome avec meilleure gestion d'erreur"""
    try:
        # Méthode 1 : Déchiffrement AES (Chrome v80+)
        iv = password[3:15]
        password = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted = cipher.decrypt(password)
        return decrypted[:-16].decode('utf-8')
    except Exception as e1:
        try:
            # Méthode 2 : Ancien format DPAPI
            return win32crypt.CryptUnprotectData(password, None, None, None, 0)[1].decode('utf-8')
        except Exception as e2:
            # Si les deux méthodes échouent, afficher plus d'infos
            return f"[Erreur déchiffrement - Longueur: {len(password)}]"

def get_encryption_key():
    """Récupère la clé de déchiffrement Chrome"""
    local_state_path = Path(os.environ['LOCALAPPDATA']) / "Google/Chrome/User Data/Local State"
    
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.loads(f.read())
    
    # Récupère et décode la clé
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:]  # Retire "DPAPI"
    
    # Déchiffre la clé avec l'API Windows
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def get_chrome_passwords():
    """Récupère et affiche les mots de passe Chrome"""
    
    # Ferme Chrome d'abord
    kill_chrome()
    
    # Vérifie que Chrome est installé
    chrome_user_data = Path(os.environ['LOCALAPPDATA']) / "Google/Chrome/User Data"
    if not chrome_user_data.exists():
        print("Chrome n'est pas installé ou les données sont introuvables.")
        return
    
    try:
        # Récupère la clé de déchiffrement
        key = get_encryption_key()
        print(f"Clé de déchiffrement récupérée (longueur: {len(key)} octets)\n")
    except Exception as e:
        print(f"Erreur lors de la récupération de la clé : {e}")
        return
    
    # Parcourt tous les profils Chrome
    profiles = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]
    
    total_passwords = 0
    passwords_decrypted = 0
    
    for profile in profiles:
        db_path = chrome_user_data / profile / "Login Data"
        
        if not db_path.exists():
            continue
            
        print(f"\n{'='*60}")
        print(f"PROFIL : {profile}")
        print(f"{'='*60}")
        
        # Copie la base de données
        temp_db = Path(os.environ['TEMP']) / f"ChromePasswords_{profile}.db"
        try:
            shutil.copy2(db_path, temp_db)
        except Exception as e:
            print(f"Impossible de copier la base de données : {e}")
            continue
        
        # Connexion à la base de données
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        try:
            # Récupère les données
            cursor.execute("SELECT origin_url, username_value, password_value, date_created FROM logins ORDER BY date_created DESC")
            
            profile_passwords = 0
            
            for origin_url, username, encrypted_password, date_created in cursor.fetchall():
                if username or encrypted_password:
                    # Tente de déchiffrer
                    if encrypted_password:
                        password = decrypt_password(encrypted_password, key)
                        if not password.startswith("[Erreur"):
                            passwords_decrypted += 1
                    else:
                        password = "[Pas de mot de passe]"
                    
                    print(f"\nSite : {origin_url}")
                    print(f"Utilisateur : {username}")
                    print(f"Mot de passe : {password}")
                    
                    # Affiche des infos de debug si erreur
                    if password.startswith("[Erreur"):
                        print(f"Debug - Taille données chiffrées : {len(encrypted_password)} octets")
                        print(f"Debug - Premiers octets : {encrypted_password[:20].hex() if encrypted_password else 'None'}")
                    
                    print("-" * 40)
                    
                    profile_passwords += 1
                    total_passwords += 1
            
            print(f"\nNombre de mots de passe dans ce profil : {profile_passwords}")
            
        except Exception as e:
            print(f"Erreur lors de la lecture de la base : {e}")
        finally:
            conn.close()
            try:
                temp_db.unlink()
            except:
                pass
    
    print(f"\n{'='*60}")
    print(f"RÉSUMÉ :")
    print(f"- Total de mots de passe trouvés : {total_passwords}")
    print(f"- Mots de passe déchiffrés avec succès : {passwords_decrypted}")
    print(f"- Mots de passe non déchiffrés : {total_passwords - passwords_decrypted}")
    print(f"{'='*60}")
    
    if total_passwords > 0:
        print("\n⚠️  ACTIONS URGENTES :")
        print("1. Changez TOUS ces mots de passe immédiatement")
        print("2. En priorité : email principal, banque, réseaux sociaux")
        print("3. Activez l'authentification à deux facteurs")
        print("4. Utilisez un gestionnaire de mots de passe")
        
        if passwords_decrypted < total_passwords:
            print("\n⚠️  Note : Certains mots de passe n'ont pas pu être déchiffrés.")
            print("Ils pourraient être dans un ancien format ou corrompus.")
            print("Par sécurité, changez TOUS vos mots de passe Chrome.")

def check_chrome_version():
    """Vérifie la version de Chrome"""
    try:
        chrome_exe = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        if not chrome_exe.exists():
            chrome_exe = Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
        
        if chrome_exe.exists():
            # Obtient la version via PowerShell
            cmd = f'(Get-Item "{chrome_exe}").VersionInfo.FileVersion'
            result = subprocess.run(["powershell", "-Command", cmd], 
                                  capture_output=True, text=True)
            version = result.stdout.strip()
            print(f"Version de Chrome détectée : {version}")
    except:
        pass

if __name__ == "__main__":
    print("=== VÉRIFICATEUR DE MOTS DE PASSE CHROME ===")
    print("Ce script va afficher vos mots de passe enregistrés dans Chrome")
    print("pour identifier ceux compromis par le malware.\n")
    
    # Vérifie la version de Chrome
    check_chrome_version()
    
    print("\n⚠️  IMPORTANT : Chrome va être fermé automatiquement.")
    response = input("Voulez-vous continuer ? (oui/non) : ")
    
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        try:
            get_chrome_passwords()
        except Exception as e:
            print(f"\nErreur générale : {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Opération annulée.")
    
    input("\nAppuyez sur Entrée pour fermer...")