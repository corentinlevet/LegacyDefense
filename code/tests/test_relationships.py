#!/usr/bin/env python3
"""
Script de test pour vérifier le calcul des relations familiales directes.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import PersonORM, FamilyORM
from core.database import DatabaseManager
from core.algorithms import GenealogyAlgorithms
from sqlalchemy.orm import sessionmaker

def test_relationships():
    """Test des relations familiales directes."""
    
    # Initialiser la base de données
    db_manager = DatabaseManager("sqlite:///geneweb.db")
    Session = sessionmaker(bind=db_manager.engine)
    session = Session()
    
    algorithms = GenealogyAlgorithms(db_manager)
    
    try:
        # Chercher des exemples de relations parent-enfant dans la base
        families = session.query(FamilyORM).filter(
            FamilyORM.father_id.isnot(None),
            FamilyORM.mother_id.isnot(None)
        ).limit(3).all()
        
        for family in families:
            print(f"\n=== Famille {family.id} ===")
            
            # Obtenir les enfants de cette famille
            children = session.query(PersonORM).filter(
                PersonORM.parent_family_id == family.id
            ).all()
            
            if children:
                father = session.query(PersonORM).filter(PersonORM.id == family.father_id).first()
                mother = session.query(PersonORM).filter(PersonORM.id == family.mother_id).first()
                
                print(f"Père: {father.first_name} {father.surname} (ID: {father.id})")
                print(f"Mère: {mother.first_name} {mother.surname} (ID: {mother.id})")
                
                for child in children[:2]:  # Tester max 2 enfants par famille
                    print(f"Enfant: {child.first_name} {child.surname} (ID: {child.id})")
                    
                    # Tester relation père-enfant
                    result_father = algorithms.calculate_relationship_distance(session, father.id, child.id)
                    print(f"  Relation père->enfant: {result_father}")
                    
                    # Tester relation enfant-père
                    result_child = algorithms.calculate_relationship_distance(session, child.id, father.id)
                    print(f"  Relation enfant->père: {result_child}")
                    
                    # Tester relation mère-enfant
                    result_mother = algorithms.calculate_relationship_distance(session, mother.id, child.id)
                    print(f"  Relation mère->enfant: {result_mother}")
                    
                    # Si il y a plusieurs enfants, tester relation frère/sœur
                    if len(children) > 1:
                        for sibling in children:
                            if sibling.id != child.id:
                                result_sibling = algorithms.calculate_relationship_distance(session, child.id, sibling.id)
                                print(f"  Relation avec {sibling.first_name}: {result_sibling}")
                                break
                    
                    print()
    
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    test_relationships()