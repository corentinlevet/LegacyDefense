#!/usr/bin/env python3
"""
Script de test pour valider les nouvelles fonctionnalités de navigation généalogique.

Ce script teste les liens familiaux et les chemins de consanguinité.
"""

import sys
import os
from sqlalchemy.orm import Session

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import DatabaseManager, PersonORM, FamilyORM
from core.algorithms import GenealogyAlgorithms


def test_relationship_navigation():
    """Test the new relationship navigation features."""
    print("=== Test de la navigation généalogique ===")
    
    # Configuration de la base de données
    database_url = "sqlite:///geneweb.db"
    db_manager = DatabaseManager(database_url)
    algorithms = GenealogyAlgorithms(db_manager)
    
    # Obtenir une session
    session = db_manager.get_session()
    
    try:
        # Trouver des personnes avec consanguinité dans nos données de test
        consanguinous_persons = session.query(PersonORM).filter(PersonORM.consang > 0).all()
        
        print(f"Personnes avec consanguinité trouvées : {len(consanguinous_persons)}")
        
        if not consanguinous_persons:
            print("❌ Aucune personne avec consanguinité trouvée !")
            return
        
        # Tester avec la première personne consanguine
        test_person = consanguinous_persons[0]
        print(f"\n📋 Test avec : {test_person.first_name} {test_person.surname}")
        print(f"   Consanguinité : {test_person.consang:.4f} ({test_person.consang * 100:.2f}%)")
        
        # Test 1 : Contexte familial
        print("\n1️⃣ Test du contexte familial...")
        family_context = algorithms.get_person_family_context(session, test_person.id)
        
        print(f"   - Parents : {len(family_context.get('parents', []))}")
        print(f"   - Enfants : {len(family_context.get('children', []))}")
        print(f"   - Frères/sœurs : {len(family_context.get('siblings', []))}")
        print(f"   - Conjoints : {len(family_context.get('spouses', []))}")
        print(f"   - Grands-parents : {len(family_context.get('grandparents', []))}")
        
        # Test 2 : Relations avec les frères et sœurs
        siblings = family_context.get('siblings', [])
        if siblings:
            print("\n2️⃣ Test des relations entre frères et sœurs...")
            sibling = siblings[0]
            print(f"   Relation entre {test_person.first_name} et {sibling.first_name}...")
            
            relationship_summary = algorithms.find_relationship_summary(
                session, test_person.id, sibling.id
            )
            
            if relationship_summary:
                print(f"   ✅ Relation trouvée : {relationship_summary.relationship_description}")
                print(f"   ✅ Type : {relationship_summary.primary_relationship.value}")
                print(f"   ✅ Chemins : {len(relationship_summary.paths)}")
                if relationship_summary.consanguinity > 0:
                    print(f"   ✅ Consanguinité : {relationship_summary.consanguinity:.4f}")
            else:
                print("   ❌ Aucune relation trouvée entre frères et sœurs")
        
        # Test 3 : Relations avec les parents
        parents = family_context.get('parents', [])
        if parents:
            print("\n3️⃣ Test des relations parent-enfant...")
            parent = parents[0]
            print(f"   Relation entre {test_person.first_name} et {parent.first_name}...")
            
            relationship_summary = algorithms.find_relationship_summary(
                session, test_person.id, parent.id
            )
            
            if relationship_summary:
                print(f"   ✅ Relation trouvée : {relationship_summary.relationship_description}")
                print(f"   ✅ Type : {relationship_summary.primary_relationship.value}")
                print(f"   ✅ Chemins : {len(relationship_summary.paths)}")
            else:
                print("   ❌ Aucune relation trouvée avec le parent")
        
        # Test 4 : Relations entre personnes consanguines (si on en a au moins 2)
        if len(consanguinous_persons) >= 2:
            print("\n4️⃣ Test des relations entre personnes consanguines...")
            person1 = consanguinous_persons[0]
            person2 = consanguinous_persons[1]
            
            print(f"   Relation entre {person1.first_name} {person1.surname} et {person2.first_name} {person2.surname}...")
            
            relationship_summary = algorithms.find_relationship_summary(
                session, person1.id, person2.id
            )
            
            if relationship_summary:
                print(f"   ✅ Relation trouvée : {relationship_summary.relationship_description}")
                print(f"   ✅ Type : {relationship_summary.primary_relationship.value}")
                print(f"   ✅ Ancêtres communs : {len(relationship_summary.common_ancestors)}")
                print(f"   ✅ Chemins : {len(relationship_summary.paths)}")
                if relationship_summary.consanguinity > 0:
                    print(f"   ✅ Consanguinité : {relationship_summary.consanguinity:.4f}")
                
                # Afficher le premier chemin en détail
                if relationship_summary.paths:
                    path = relationship_summary.paths[0]
                    print(f"   📍 Premier chemin : {path.person1_distance} + {path.person2_distance} générations")
                    print(f"      Type de chemin : {path.path_type}")
                    print(f"      Via l'ancêtre : ID {path.common_ancestor_id}")
            else:
                print("   ❌ Aucune relation trouvée entre personnes consanguines")
        
        # Test 5 : Chemins détaillés
        print("\n5️⃣ Test des chemins détaillés...")
        if len(consanguinous_persons) >= 2:
            person1 = consanguinous_persons[0]
            person2 = consanguinous_persons[1]
            
            detailed_paths = algorithms.find_detailed_relationship_paths(
                session, person1.id, person2.id
            )
            
            print(f"   Chemins détaillés trouvés : {len(detailed_paths)}")
            
            for i, path in enumerate(detailed_paths[:3]):  # Afficher les 3 premiers
                print(f"   📍 Chemin {i+1} :")
                print(f"      Ancêtre commun : ID {path.common_ancestor_id}")
                print(f"      Distance 1 : {path.person1_distance} générations")
                print(f"      Distance 2 : {path.person2_distance} générations")
                print(f"      Type : {path.path_type}")
                print(f"      Description : {path.relationship_name}")
        
        # Test 6 : Performance et cache
        print("\n6️⃣ Test des performances et du cache...")
        cache_stats = algorithms.get_cache_stats()
        print(f"   Cache de consanguinité : {cache_stats['consanguinity_cache_size']} entrées")
        print(f"   Cache d'ancêtres : {cache_stats['ancestor_cache_size']} entrées")
        print(f"   Cache de descendants : {cache_stats['descendant_cache_size']} entrées")
        print(f"   Taux de réussite : {cache_stats['hit_rate']:.2%}")
        
        print("\n✅ Tests de navigation généalogique terminés avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests : {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        session.close()


def test_specific_relationships():
    """Test avec des personnes spécifiques de nos données de test."""
    print("\n=== Test de relations spécifiques ===")
    
    database_url = "sqlite:///geneweb.db"
    db_manager = DatabaseManager(database_url)
    algorithms = GenealogyAlgorithms(db_manager)
    session = db_manager.get_session()
    
    try:
        # Chercher les personnes de nos données de test par nom
        jean_albert = session.query(PersonORM).filter(
            PersonORM.first_name == "Jean",
            PersonORM.surname == "DUBOIS",
            PersonORM.consang > 0
        ).first()
        
        marie_albert = session.query(PersonORM).filter(
            PersonORM.first_name == "Marie",
            PersonORM.surname == "DUBOIS",
            PersonORM.consang > 0
        ).first()
        
        if jean_albert and marie_albert:
            print(f"Test avec Jean DUBOIS (ID: {jean_albert.id}) et Marie DUBOIS (ID: {marie_albert.id})")
            
            # Ces deux personnes devraient être frères et sœurs avec consanguinité
            relationship_summary = algorithms.find_relationship_summary(
                session, jean_albert.id, marie_albert.id
            )
            
            if relationship_summary:
                print(f"✅ Relation : {relationship_summary.relationship_description}")
                print(f"✅ Type : {relationship_summary.primary_relationship.value}")
                print(f"✅ Ancêtres communs : {len(relationship_summary.common_ancestors)}")
                
                # Afficher les ancêtres communs
                for ancestor_id in relationship_summary.common_ancestors:
                    ancestor = session.query(PersonORM).filter(PersonORM.id == ancestor_id).first()
                    if ancestor:
                        print(f"   📍 Ancêtre commun : {ancestor.first_name} {ancestor.surname} (ID: {ancestor.id})")
            else:
                print("❌ Aucune relation trouvée")
        else:
            print("❌ Personnes de test spécifiques non trouvées")
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        session.close()


def main():
    """Fonction principale."""
    print("🧬 Test des fonctionnalités de navigation généalogique")
    print("=" * 60)
    
    test_relationship_navigation()
    test_specific_relationships()
    
    print("\n🎉 Tests terminés !")
    print("\n💡 Conseil : Visitez http://localhost:8000 pour tester l'interface web")
    print("   - Allez sur une personne avec consanguinité")
    print("   - Cliquez sur 'Relations' pour voir les liens familiaux")
    print("   - Cliquez sur 'Relation' à côté d'un parent/frère pour voir le chemin détaillé")


if __name__ == "__main__":
    main()