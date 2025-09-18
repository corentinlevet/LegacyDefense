#!/usr/bin/env python3
"""
Script de test pour déboguer les descendants.
"""
import os
import sys

# S'assurer qu'on est dans le bon répertoire
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

from core.webapp import GeneWebApp
from core.database import DatabaseManager

def test_descendants():
    """Test la fonction get_descendants_by_generation."""
    print("🧪 Test des descendants...")
    
    # Créer l'app
    db_manager = DatabaseManager("sqlite:///geneweb.db")
    from core.algorithms import GenealogyAlgorithms
    algorithms = GenealogyAlgorithms(db_manager)
    
    # Tester avec la personne ID 1
    with db_manager.get_session() as session:
        print(f"📋 Test avec personne ID=1")
        
        # Test de l'ancienne méthode
        old_descendants = algorithms.get_descendants(session, 1, 3)
        print(f"   Ancienne méthode (IDs): {len(old_descendants)} descendants")
        print(f"   IDs: {list(old_descendants)[:10]}...")  # Premiers 10
        
        # Test de la nouvelle méthode
        try:
            new_descendants = algorithms.get_descendants_by_generation(session, 1, 3)
            print(f"   Nouvelle méthode: {len(new_descendants)} générations")
            for i, generation in enumerate(new_descendants):
                print(f"     Génération {i+1}: {len(generation)} personnes")
                if generation:
                    person_names = [f"{p.first_name} {p.surname}" for p in generation[:3]]
                    print(f"       Ex: {', '.join(person_names)}...")
        except Exception as e:
            print(f"   ❌ Erreur dans nouvelle méthode: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_descendants()