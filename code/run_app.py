#!/usr/bin/env python3
"""
Script pour démarrer l'application GeneWeb avec le bon répertoire de travail.
"""
import os
import sys

# S'assurer qu'on est dans le bon répertoire
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"📁 Répertoire de travail : {os.getcwd()}")

# Ajouter le répertoire au PYTHONPATH
sys.path.insert(0, script_dir)

# Lancer l'application
from core.webapp import GeneWebApp
import uvicorn

def main():
    """Start the GeneWeb application."""
    print("🚀 Démarrage de GeneWeb...")
    
    # Vérifier les templates
    templates_dir = os.path.join(script_dir, "templates")
    if os.path.exists(templates_dir):
        print(f"📋 Templates disponibles dans {templates_dir}:")
        for template in os.listdir(templates_dir):
            print(f"   - {template}")
    else:
        print(f"   ❌ Répertoire templates non trouvé: {templates_dir}")
    
    # Create app instance
    app_instance = GeneWebApp("sqlite:///geneweb.db")
    
    # Start server
    print("🌐 Démarrage du serveur sur http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        app_instance.app, 
        host="0.0.0.0", 
        port=8001,
        reload=False
    )

if __name__ == "__main__":
    main()