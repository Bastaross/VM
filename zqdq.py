#!/usr/bin/env python3
import os
import time
import shutil
from datetime import datetime

def monitor_appdata(filename='gruppe.py', interval=5):
    """
    Surveille en boucle %APPDATA% pour détecter l'apparition ou la modification de `filename`.
    Dès qu'il est trouvé/modifié, le script le copie dans ./captured/ et affiche son contenu.
    """
    appdata = os.getenv('APPDATA')
    if not appdata:
        print("Erreur : la variable d'environnement APPDATA n'est pas définie.")
        return

    target_path = os.path.join(appdata, filename)
    last_mtime = None

    # Dossier local pour sauvegarder les copies
    base_dir = os.path.dirname(os.path.abspath(__file__))
    captured_dir = os.path.join(base_dir, 'captured')
    os.makedirs(captured_dir, exist_ok=True)

    print(f"🔍 Surveillance de {target_path} toutes les {interval}s. Ctrl+C pour arrêter.\n")

    try:
        while True:
            if os.path.isfile(target_path):
                mtime = os.path.getmtime(target_path)
                # Nouveau fichier ou fichier modifié depuis la dernière fois
                if last_mtime is None or mtime > last_mtime:
                    last_mtime = mtime
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    dest_name = f"{filename.rstrip('.py')}_{timestamp}.py"
                    dest_path = os.path.join(captured_dir, dest_name)

                    # Copier le fichier
                    shutil.copy2(target_path, dest_path)
                    print(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] → Détecté {filename}, copie vers :")
                    print(f"    {dest_path}\n")

                    # Afficher le contenu
                    try:
                        with open(dest_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        print("----- Contenu de la copie -----")
                        print(content)
                        print("----- Fin du contenu -----\n")
                    except Exception as e:
                        print(f"Erreur lors de la lecture de {dest_path}: {e}\n")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 Surveillance interrompue par l'utilisateur.")

if __name__ == '__main__':
    monitor_appdata()
