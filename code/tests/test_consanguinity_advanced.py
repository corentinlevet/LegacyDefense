"""
Tests avancés pour le calcul de consanguinité selon l'algorithme de Didier Rémy.
Implémentation TDD des fonctionnalités manquantes.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, Set, List

from core.database import DatabaseManager, PersonORM, FamilyORM, Base
from core.models import Sex
from core.algorithms import GenealogyAlgorithms, ConsanguinityResult


class TestAdvancedConsanguinity:
    """Test du calcul de consanguinité avancé avec l'algorithme de Didier Rémy."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.engine = engine
        db_manager.SessionLocal = SessionLocal
        
        yield db_manager
    
    def test_simple_consanguinity_calculation(self, temp_db):
        """Test RED: Calcul de consanguinité simple entre frère et sœur."""
        # RED: Ce test doit échouer car l'algorithme complet n'est pas implémenté
        
        with temp_db.get_session() as session:
            algorithms = GenealogyAlgorithms(temp_db)
            
            # Créer une famille simple : parents et leurs enfants (frère/sœur)
            # Parents
            father = PersonORM(id=1, first_name="Jean", surname="Dupont", sex=Sex.MALE)
            mother = PersonORM(id=2, first_name="Marie", surname="Durand", sex=Sex.FEMALE)
            
            # Enfants
            son = PersonORM(id=3, first_name="Pierre", surname="Dupont", sex=Sex.MALE)
            daughter = PersonORM(id=4, first_name="Anne", surname="Dupont", sex=Sex.FEMALE)
            
            # Famille
            family = FamilyORM(id=1, father_id=1, mother_id=2)
            
            session.add_all([father, mother, son, daughter, family])
            
            # Lier les enfants à la famille
            son.parent_family_id = 1
            daughter.parent_family_id = 1
            
            session.commit()
            
            # Test : les enfants d'un même couple qui se marient
            # (consanguinité = 0.25 = 1/4)
            child_family = FamilyORM(id=2, father_id=3, mother_id=4)
            child = PersonORM(id=5, first_name="Enfant", surname="Dupont", sex=Sex.MALE)
            child.parent_family_id = 2
            
            session.add_all([child_family, child])
            session.commit()
            
            # Calculer la consanguinité de l'enfant
            result = algorithms.calculate_consanguinity_advanced(session, 5)
            
            # RED: Ce test doit échouer car la méthode n'existe pas encore
            assert isinstance(result, ConsanguinityResult)
            assert abs(result.consanguinity - 0.25) < 0.001  # Tolérance pour les flottants
            assert len(result.common_ancestors) == 2  # Les grands-parents
    
    def test_topological_sort_for_consanguinity(self, temp_db):
        """Test RED: Tri topologique des personnes pour calcul correct."""
        # RED: Ce test doit échouer car l'algorithme de tri topologique n'existe pas
        
        with temp_db.get_session() as session:
            algorithms = GenealogyAlgorithms(temp_db)
            
            # Créer une généalogie sur 3 générations
            persons = [
                PersonORM(id=1, first_name="GP1", surname="A", sex=Sex.MALE),    # Grand-père
                PersonORM(id=2, first_name="GM1", surname="B", sex=Sex.FEMALE),  # Grand-mère
                PersonORM(id=3, first_name="P1", surname="A", sex=Sex.MALE),     # Père
                PersonORM(id=4, first_name="P2", surname="C", sex=Sex.FEMALE),   # Mère
                PersonORM(id=5, first_name="E1", surname="A", sex=Sex.MALE),     # Enfant
            ]
            
            families = [
                FamilyORM(id=1, father_id=1, mother_id=2),  # Grands-parents
                FamilyORM(id=2, father_id=3, mother_id=4),  # Parents
            ]
            
            session.add_all(persons + families)
            
            # Liens familiaux
            persons[2].parent_family_id = 1  # Père est enfant des grands-parents
            persons[4].parent_family_id = 2  # Enfant est enfant des parents
            
            session.commit()
            
            # RED: Cette méthode n'existe pas encore
            sorted_persons = algorithms.topological_sort_persons(session)
            
            # Les grands-parents doivent venir avant les parents, qui viennent avant les enfants
            person_ids = [p.id for p in sorted_persons]
            
            # Vérifier l'ordre topologique
            assert person_ids.index(1) < person_ids.index(3)  # Grand-père avant père
            assert person_ids.index(2) < person_ids.index(3)  # Grand-mère avant père
            assert person_ids.index(3) < person_ids.index(5)  # Père avant enfant
            assert person_ids.index(4) < person_ids.index(5)  # Mère avant enfant
    
    def test_complex_consanguinity_multiple_paths(self, temp_db):
        """Test RED: Consanguinité avec chemins multiples vers ancêtres communs."""
        # RED: Ce test doit échouer car l'algorithme complet n'est pas implémenté
        
        with temp_db.get_session() as session:
            algorithms = GenealogyAlgorithms(temp_db)
            
            # Créer une situation où les parents ont des ancêtres communs 
            # par plusieurs chemins (implexe)
            
            # Ancêtre commun
            common_ancestor = PersonORM(id=1, first_name="Ancêtre", surname="Commun", sex=Sex.MALE)
            common_spouse = PersonORM(id=2, first_name="Épouse", surname="Commune", sex=Sex.FEMALE)
            
            # Leurs enfants (qui seront frère et sœur)
            child1 = PersonORM(id=3, first_name="Enfant1", surname="Commun", sex=Sex.MALE)
            child2 = PersonORM(id=4, first_name="Enfant2", surname="Commun", sex=Sex.FEMALE)
            
            # Descendants de child1
            grand_child1 = PersonORM(id=5, first_name="PetitEnfant1", surname="A", sex=Sex.MALE)
            # Descendants de child2  
            grand_child2 = PersonORM(id=6, first_name="PetitEnfant2", surname="B", sex=Sex.FEMALE)
            
            # L'enfant issu du mariage des petits-enfants (cousins)
            final_child = PersonORM(id=7, first_name="Final", surname="AB", sex=Sex.MALE)
            
            families = [
                FamilyORM(id=1, father_id=1, mother_id=2),  # Ancêtres communs
                FamilyORM(id=2, father_id=3, mother_id=None),  # Child1 (père célibataire pour simplifier)
                FamilyORM(id=3, father_id=4, mother_id=None),  # Child2 (parent célibataire pour simplifier)
                FamilyORM(id=4, father_id=5, mother_id=6),  # Mariage des cousins
            ]
            
            session.add_all([common_ancestor, common_spouse, child1, child2, 
                           grand_child1, grand_child2, final_child] + families)
            
            # Liens familiaux
            child1.parent_family_id = 1
            child2.parent_family_id = 1
            grand_child1.parent_family_id = 2
            grand_child2.parent_family_id = 3
            final_child.parent_family_id = 4
            
            session.commit()
            
            # RED: Ce test doit échouer car l'algorithme n'est pas complet
            result = algorithms.calculate_consanguinity_advanced(session, 7)
            
            # Consanguinité pour mariage entre cousins germains = 1/16 = 0.0625
            assert isinstance(result, ConsanguinityResult)
            assert abs(result.consanguinity - 0.0625) < 0.001
            assert len(result.common_ancestors) == 2  # Les ancêtres communs
    
    def test_consanguinity_with_loops_detection(self, temp_db):
        """Test RED: Détection et gestion des boucles dans l'arbre généalogique."""
        # RED: Ce test doit échouer car la détection de boucles n'est pas implémentée
        
        with temp_db.get_session() as session:
            algorithms = GenealogyAlgorithms(temp_db)
            
            # Créer une situation avec boucle (impossible en réalité mais peut arriver dans les données)
            persons = [
                PersonORM(id=1, first_name="A", surname="Test", sex=Sex.MALE),
                PersonORM(id=2, first_name="B", surname="Test", sex=Sex.FEMALE),
                PersonORM(id=3, first_name="C", surname="Test", sex=Sex.MALE),
            ]
            
            families = [
                FamilyORM(id=1, father_id=1, mother_id=2),
                FamilyORM(id=2, father_id=3, mother_id=1),  # Boucle : A est père de C et C est père de A
            ]
            
            session.add_all(persons + families)
            
            # Créer la boucle
            persons[2].parent_family_id = 1  # C est enfant de A et B
            persons[0].parent_family_id = 2  # A est enfant de C (BOUCLE!)
            
            session.commit()
            
            # RED: Cette méthode de détection n'existe pas encore
            has_loops = algorithms.detect_genealogical_loops(session)
            
            assert has_loops is True
            
            # La méthode devrait lever une exception ou retourner une erreur
            with pytest.raises(ValueError, match="Boucle détectée"):
                algorithms.calculate_consanguinity_advanced(session, 1)
    
    def test_mass_consanguinity_computation(self, temp_db):
        """Test RED: Calcul de consanguinité en masse pour toute la base."""
        # RED: Ce test doit échouer car la méthode de calcul en masse n'existe pas
        
        with temp_db.get_session() as session:
            algorithms = GenealogyAlgorithms(temp_db)
            
            # Créer une base de données avec plusieurs familles
            persons = []
            families = []
            
            # Famille 1
            for i in range(1, 6):  # 5 personnes
                persons.append(PersonORM(
                    id=i, 
                    first_name=f"Person{i}", 
                    surname="Family1",
                    sex=Sex.MALE if i % 2 == 1 else Sex.FEMALE
                ))
            
            families.append(FamilyORM(id=1, father_id=1, mother_id=2))
            families.append(FamilyORM(id=2, father_id=3, mother_id=4))
            
            # Liens
            persons[2].parent_family_id = 1  # Person3 enfant de 1 et 2
            persons[3].parent_family_id = 1  # Person4 enfant de 1 et 2
            persons[4].parent_family_id = 2  # Person5 enfant de 3 et 4 (frère et sœur)
            
            session.add_all(persons + families)
            session.commit()
            
            # RED: Cette méthode n'existe pas encore
            results = algorithms.compute_all_consanguinity_advanced(
                session, 
                from_scratch=True, 
                verbosity=1
            )
            
            assert isinstance(results, dict)
            assert len(results) == 5  # Un résultat par personne
            assert results[5] > 0.0  # Person5 a de la consanguinité (parents frère/sœur)
            assert all(results[i] == 0.0 for i in [1, 2, 3, 4])  # Autres sans consanguinité
    
    def test_consanguinity_caching_system(self, temp_db):
        """Test RED: Système de cache pour optimiser les calculs répétitifs."""
        # RED: Ce test doit échouer car le système de cache n'est pas implémenté
        
        with temp_db.get_session() as session:
            algorithms = GenealogyAlgorithms(temp_db)
            
            # Créer une famille simple
            persons = [
                PersonORM(id=1, first_name="Father", surname="Test", sex=Sex.MALE),
                PersonORM(id=2, first_name="Mother", surname="Test", sex=Sex.FEMALE),
                PersonORM(id=3, first_name="Child", surname="Test", sex=Sex.MALE),
            ]
            
            family = FamilyORM(id=1, father_id=1, mother_id=2)
            persons[2].parent_family_id = 1
            
            session.add_all(persons + [family])
            session.commit()
            
            # RED: Ces méthodes de cache n'existent pas encore
            algorithms.clear_consanguinity_cache()
            
            # Premier calcul (doit être mis en cache)
            result1 = algorithms.calculate_consanguinity_advanced(session, 3)
            cache_hits_before = algorithms.get_cache_stats()['hits']
            
            # Deuxième calcul (doit utiliser le cache)
            result2 = algorithms.calculate_consanguinity_advanced(session, 3)
            cache_hits_after = algorithms.get_cache_stats()['hits']
            
            assert result1.consanguinity == result2.consanguinity
            assert cache_hits_after > cache_hits_before  # Le cache a été utilisé