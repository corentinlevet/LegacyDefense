#!/usr/bin/env python3
"""
Script pour corriger les appels de traduction dans relationships.html
Remplace _("key", "default") par "default"
"""

import re

def fix_i18n_calls(file_path):
    """Corrige les appels de traduction avec 2 arguments."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour matcher _("key", "value")
    pattern = r'_\(["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']\)'
    
    # Remplacer par "value" directement
    def replace_match(match):
        key = match.group(1)
        value = match.group(2)
        print(f"Remplaçant _(\"{key}\", \"{value}\") par \"{value}\"")
        return f'"{value}"'
    
    new_content = re.sub(pattern, replace_match, content)
    
    # Sauvegarder le fichier
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Corrections appliquées à {file_path}")

if __name__ == "__main__":
    file_path = "templates/relationships.html"
    print(f"🔧 Correction des appels i18n dans {file_path}")
    fix_i18n_calls(file_path)
    
    # Aussi corriger relationship_between.html s'il existe
    import os
    if os.path.exists("templates/relationship_between.html"):
        print(f"🔧 Correction des appels i18n dans templates/relationship_between.html")
        fix_i18n_calls("templates/relationship_between.html")