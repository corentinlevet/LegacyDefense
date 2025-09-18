#!/usr/bin/env python3
"""
Script pour nettoyer tous les appels de traduction dans tous les templates.
Remplace _("key", "default") par "default"
"""

import re
import os
import glob

def fix_i18n_calls_in_file(file_path):
    """Corrige les appels de traduction avec 2 arguments dans un fichier."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"⚠️  Erreur de décodage pour {file_path}, ignoré")
        return False
    
    # Pattern pour matcher _("key", "value")
    pattern = r'_\(["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']\)'
    
    original_content = content
    
    # Remplacer par "value" directement
    def replace_match(match):
        key = match.group(1)
        value = match.group(2)
        print(f"   Remplaçant _(\"{key}\", \"{value}\") par \"{value}\"")
        return f'"{value}"'
    
    new_content = re.sub(pattern, replace_match, content)
    
    if new_content != original_content:
        # Sauvegarder le fichier
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Corrections appliquées à {file_path}")
        return True
    else:
        print(f"📄 Aucune correction nécessaire pour {file_path}")
        return False

def main():
    """Nettoie tous les templates."""
    templates_dir = "templates"
    
    if not os.path.exists(templates_dir):
        print(f"❌ Répertoire {templates_dir} non trouvé")
        return
    
    # Chercher tous les fichiers .html
    html_files = glob.glob(os.path.join(templates_dir, "*.html"))
    
    if not html_files:
        print(f"❌ Aucun fichier .html trouvé dans {templates_dir}")
        return
    
    print(f"🔧 Nettoyage des appels i18n dans {len(html_files)} templates...")
    
    total_fixed = 0
    for file_path in html_files:
        print(f"\n📋 Traitement de {file_path}:")
        if fix_i18n_calls_in_file(file_path):
            total_fixed += 1
    
    print(f"\n🎉 Terminé ! {total_fixed}/{len(html_files)} fichiers modifiés")

if __name__ == "__main__":
    main()