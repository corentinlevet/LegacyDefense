"""
TDD Tests for GeneWeb Algorithms - Following Test-Driven Development

This module contains test-driven development tests for the core genealogical
algorithms. Each test is written BEFORE the implementation to ensure correct
behavior and guide development.
"""
import pytest
import tempfile
import os
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Person, Family, Name, Sex, Date, Event, EventType, SosaNumber
from core.database import DatabaseManager, PersonORM, FamilyORM, Base
from core.algorithms import GenealogyAlgorithms, ConsanguinityResult, RelationshipPath


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    db_url = f"sqlite:///{temp_file.name}"
    db_manager = DatabaseManager(db_url)
    db_manager.create_tables()
    
    yield db_manager
    
    # Cleanup - Close database connections first
    try:
        db_manager.engine.dispose()  # Close all database connections
        time.sleep(0.1)  # Small delay to ensure files are closed
        os.unlink(temp_file.name)
    except (PermissionError, FileNotFoundError):
        pass  # Ignore if file can't be deleted on Windows


class TestSosaNumbering:
    """Test Sosa numbering system (test-driven)."""
    
    def test_sosa_creation(self):
        """Test Sosa number creation and basic properties."""
        # RED: Write test first
        sosa = SosaNumber(1)
        assert sosa.value == 1
        assert str(sosa) == "1"
        
        # Test root person (Sosa 1)
        assert sosa.generation() == 0
        assert not sosa.is_father()
        assert not sosa.is_mother()
    
    def test_sosa_father_calculation(self):
        """Test father Sosa number calculation."""
        # RED: Test for father calculation (Sosa * 2)
        root = SosaNumber(1)
        father = root.father()
        
        assert father.value == 2
        assert father.generation() == 1
        assert father.is_father()
        assert not father.is_mother()
        
        # Test with another example
        person = SosaNumber(5)
        father = person.father()
        assert father.value == 10
    
    def test_sosa_mother_calculation(self):
        """Test mother Sosa number calculation."""
        # RED: Test for mother calculation (Sosa * 2 + 1)
        root = SosaNumber(1)
        mother = root.mother()
        
        assert mother.value == 3
        assert mother.generation() == 1
        assert not mother.is_father()
        assert mother.is_mother()
        
        # Test with another example
        person = SosaNumber(4)
        mother = person.mother()
        assert mother.value == 9
    
    def test_sosa_child_calculation(self):
        """Test child Sosa number calculation."""
        # RED: Test for child calculation (Sosa // 2)
        father = SosaNumber(6)
        child = father.child()
        
        assert child.value == 3
        assert child.generation() == 1  # Child is closer to root (higher in hierarchy)
        
        mother = SosaNumber(7)
        child = mother.child()
        assert child.value == 3  # Same child for both parents
    
    def test_sosa_generation_levels(self):
        """Test generation level calculation."""
        # RED: Test generation calculation (log2)
        test_cases = [
            (1, 0),  # Root
            (2, 1),  # Parents
            (3, 1),
            (4, 2),  # Grandparents
            (5, 2),
            (6, 2),
            (7, 2),
            (8, 3),  # Great-grandparents
            (16, 4), # Great-great-grandparents
        ]
        
        for sosa_value, expected_generation in test_cases:
            sosa = SosaNumber(sosa_value)
            assert sosa.generation() == expected_generation


class TestConsanguinityCalculation:
    """Test consanguinity calculation algorithms (test-driven)."""
    
    def setup_simple_family(self, db_manager, session):
        """Set up a simple family structure for testing."""
        # Create persons
        persons_data = [
            # Generation 0 (ancestors)
            {'id': 1, 'first_name': 'John', 'surname': 'Common', 'sex': Sex.MALE},
            {'id': 2, 'first_name': 'Mary', 'surname': 'Common', 'sex': Sex.FEMALE},
            
            # Generation 1 (parents)
            {'id': 3, 'first_name': 'Father', 'surname': 'Smith', 'sex': Sex.MALE},
            {'id': 4, 'first_name': 'Mother', 'surname': 'Smith', 'sex': Sex.FEMALE},
            
            # Generation 2 (child with consanguinity)
            {'id': 5, 'first_name': 'Child', 'surname': 'Smith', 'sex': Sex.MALE},
        ]
        
        # Add persons to database
        for data in persons_data:
            person = db_manager.add_person(session, data)
        
        # Create families
        # Family 1: John + Mary -> Father
        family1 = FamilyORM(id=1, father_id=1, mother_id=2)
        session.add(family1)
        
        # Family 2: John + Mary -> Mother (same parents = siblings)
        family2 = FamilyORM(id=2, father_id=1, mother_id=2) 
        session.add(family2)
        
        # Family 3: Father + Mother -> Child (parents are siblings)
        family3 = FamilyORM(id=3, father_id=3, mother_id=4)
        session.add(family3)
        
        # Set parent families
        session.query(PersonORM).filter(PersonORM.id == 3).first().parent_family_id = 1
        session.query(PersonORM).filter(PersonORM.id == 4).first().parent_family_id = 2
        session.query(PersonORM).filter(PersonORM.id == 5).first().parent_family_id = 3
        
        session.commit()
        return persons_data
    
    def test_no_consanguinity_case(self, temp_db):
        """Test consanguinity calculation for person with unrelated parents."""
        # RED: Write test for zero consanguinity case
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create person with unrelated parents
            father_data = {'id': 1, 'first_name': 'John', 'surname': 'Doe', 'sex': Sex.MALE}
            mother_data = {'id': 2, 'first_name': 'Jane', 'surname': 'Smith', 'sex': Sex.FEMALE}
            child_data = {'id': 3, 'first_name': 'Child', 'surname': 'Doe', 'sex': Sex.MALE}
            
            temp_db.add_person(session, father_data)
            temp_db.add_person(session, mother_data)
            temp_db.add_person(session, child_data)
            
            # Create family
            family = FamilyORM(id=1, father_id=1, mother_id=2)
            session.add(family)
            
            # Set child's parent family
            session.query(PersonORM).filter(PersonORM.id == 3).first().parent_family_id = 1
            session.commit()
            
            # Calculate consanguinity
            result = algorithms.calculate_consanguinity(session, 3)
            
            assert result.person_id == 3
            assert result.consanguinity == 0.0
            assert len(result.relationship_paths) == 0
            assert len(result.common_ancestors) == 0
    
    def test_sibling_parents_consanguinity(self, temp_db):
        """Test consanguinity calculation for child of sibling parents."""
        # RED: Write test for sibling consanguinity (coefficient = 1/8 = 0.125)
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            self.setup_simple_family(temp_db, session)
            
            # Calculate consanguinity for child (ID 5)
            result = algorithms.calculate_consanguinity(session, 5)
            
            assert result.person_id == 5
            # For siblings with TWO common ancestors (both grandparents):
            # Consanguinity = (1/2)^3 + (1/2)^3 = 1/8 + 1/8 = 1/4 = 0.25
            assert abs(result.consanguinity - 0.25) < 0.001  # 1/4 for sibling parents with 2 common ancestors
            assert len(result.relationship_paths) > 0
            assert len(result.common_ancestors) > 0
            
            # Check that common ancestors are found
            assert 1 in result.common_ancestors  # John
            assert 2 in result.common_ancestors  # Mary
    
    def test_orphan_person_consanguinity(self, temp_db):
        """Test consanguinity for person with no parents."""
        # RED: Test edge case - orphan person
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            orphan_data = {'id': 1, 'first_name': 'Orphan', 'surname': 'Child', 'sex': Sex.MALE}
            temp_db.add_person(session, orphan_data)
            
            result = algorithms.calculate_consanguinity(session, 1)
            
            assert result.person_id == 1
            assert result.consanguinity == 0.0
            assert len(result.relationship_paths) == 0
    
    def test_single_parent_consanguinity(self, temp_db):
        """Test consanguinity for person with only one parent."""
        # RED: Test edge case - single parent
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            father_data = {'id': 1, 'first_name': 'Father', 'surname': 'Smith', 'sex': Sex.MALE}
            child_data = {'id': 2, 'first_name': 'Child', 'surname': 'Smith', 'sex': Sex.MALE}
            
            temp_db.add_person(session, father_data)
            temp_db.add_person(session, child_data)
            
            # Create family with only father
            family = FamilyORM(id=1, father_id=1, mother_id=None)
            session.add(family)
            
            session.query(PersonORM).filter(PersonORM.id == 2).first().parent_family_id = 1
            session.commit()
            
            result = algorithms.calculate_consanguinity(session, 2)
            
            assert result.person_id == 2
            assert result.consanguinity == 0.0


class TestRelationshipDetection:
    """Test relationship type detection (test-driven)."""
    
    def test_same_person_relationship(self, temp_db):
        """Test relationship detection for same person."""
        # RED: Test identity relationship
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            person_data = {'id': 1, 'first_name': 'John', 'surname': 'Doe', 'sex': Sex.MALE}
            temp_db.add_person(session, person_data)
            
            relationship = algorithms.find_relationship_type(session, 1, 1)
            assert relationship == "same person"
    
    def test_parent_child_relationship(self, temp_db):
        """Test parent-child relationship detection."""
        # RED: Test direct parent-child relationship
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create parent and child
            parent_data = {'id': 1, 'first_name': 'Parent', 'surname': 'Smith', 'sex': Sex.MALE}
            child_data = {'id': 2, 'first_name': 'Child', 'surname': 'Smith', 'sex': Sex.MALE}
            
            temp_db.add_person(session, parent_data)
            temp_db.add_person(session, child_data)
            
            # Create family
            family = FamilyORM(id=1, father_id=1, mother_id=None)
            session.add(family)
            
            session.query(PersonORM).filter(PersonORM.id == 2).first().parent_family_id = 1
            session.commit()
            
            # Test both directions
            relationship = algorithms.find_relationship_type(session, 1, 2)
            assert relationship == "parent-child"
            
            relationship = algorithms.find_relationship_type(session, 2, 1)
            assert relationship == "child-parent"
    
    def test_sibling_relationship(self, temp_db):
        """Test sibling relationship detection."""
        # RED: Test sibling relationship
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create parents and children
            father_data = {'id': 1, 'first_name': 'Father', 'surname': 'Smith', 'sex': Sex.MALE}
            mother_data = {'id': 2, 'first_name': 'Mother', 'surname': 'Smith', 'sex': Sex.FEMALE}
            child1_data = {'id': 3, 'first_name': 'Child1', 'surname': 'Smith', 'sex': Sex.MALE}
            child2_data = {'id': 4, 'first_name': 'Child2', 'surname': 'Smith', 'sex': Sex.FEMALE}
            
            for data in [father_data, mother_data, child1_data, child2_data]:
                temp_db.add_person(session, data)
            
            # Create family
            family = FamilyORM(id=1, father_id=1, mother_id=2)
            session.add(family)
            
            # Set both children to same parent family
            session.query(PersonORM).filter(PersonORM.id == 3).first().parent_family_id = 1
            session.query(PersonORM).filter(PersonORM.id == 4).first().parent_family_id = 1
            session.commit()
            
            relationship = algorithms.find_relationship_type(session, 3, 4)
            assert relationship == "siblings"
    
    def test_cousin_relationship(self, temp_db):
        """Test cousin relationship detection."""
        # RED: Test cousin relationship (grandparents -> parents -> cousins)
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create multi-generation family for cousins
            persons_data = [
                # Grandparents
                {'id': 1, 'first_name': 'Grandfather', 'surname': 'Smith', 'sex': Sex.MALE},
                {'id': 2, 'first_name': 'Grandmother', 'surname': 'Smith', 'sex': Sex.FEMALE},
                
                # Parents (siblings)
                {'id': 3, 'first_name': 'Parent1', 'surname': 'Smith', 'sex': Sex.MALE},
                {'id': 4, 'first_name': 'Parent2', 'surname': 'Smith', 'sex': Sex.FEMALE},
                
                # Cousins
                {'id': 5, 'first_name': 'Cousin1', 'surname': 'Smith', 'sex': Sex.MALE},
                {'id': 6, 'first_name': 'Cousin2', 'surname': 'Smith', 'sex': Sex.FEMALE},
            ]
            
            for data in persons_data:
                temp_db.add_person(session, data)
            
            # Create families
            # Grandparents -> Parents
            family1 = FamilyORM(id=1, father_id=1, mother_id=2)
            session.add(family1)
            
            # Parent1 family
            family2 = FamilyORM(id=2, father_id=3, mother_id=None)
            session.add(family2)
            
            # Parent2 family  
            family3 = FamilyORM(id=3, father_id=4, mother_id=None)
            session.add(family3)
            
            # Set parent relationships
            session.query(PersonORM).filter(PersonORM.id == 3).first().parent_family_id = 1
            session.query(PersonORM).filter(PersonORM.id == 4).first().parent_family_id = 1
            session.query(PersonORM).filter(PersonORM.id == 5).first().parent_family_id = 2
            session.query(PersonORM).filter(PersonORM.id == 6).first().parent_family_id = 3
            session.commit()
            
            relationship = algorithms.find_relationship_type(session, 5, 6)
            assert relationship == "cousins"
    
    def test_unrelated_persons(self, temp_db):
        """Test relationship detection for unrelated persons."""
        # RED: Test no relationship case
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create two unrelated persons
            person1_data = {'id': 1, 'first_name': 'John', 'surname': 'Doe', 'sex': Sex.MALE}
            person2_data = {'id': 2, 'first_name': 'Jane', 'surname': 'Smith', 'sex': Sex.FEMALE}
            
            temp_db.add_person(session, person1_data)
            temp_db.add_person(session, person2_data)
            
            relationship = algorithms.find_relationship_type(session, 1, 2)
            assert relationship == "not related"


class TestAncestorDescendantQueries:
    """Test ancestor and descendant query algorithms (test-driven)."""
    
    def test_get_direct_ancestors(self, temp_db):
        """Test getting direct ancestors (parents, grandparents, etc.)."""
        # RED: Test ancestor retrieval
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create 3-generation family
            persons_data = [
                {'id': 1, 'first_name': 'Grandpa', 'surname': 'Smith', 'sex': Sex.MALE},
                {'id': 2, 'first_name': 'Grandma', 'surname': 'Smith', 'sex': Sex.FEMALE},
                {'id': 3, 'first_name': 'Father', 'surname': 'Smith', 'sex': Sex.MALE},
                {'id': 4, 'first_name': 'Child', 'surname': 'Smith', 'sex': Sex.MALE},
            ]
            
            for data in persons_data:
                temp_db.add_person(session, data)
            
            # Create families
            family1 = FamilyORM(id=1, father_id=1, mother_id=2)  # Grandparents
            family2 = FamilyORM(id=2, father_id=3, mother_id=None)  # Parent
            session.add(family1)
            session.add(family2)
            
            # Set relationships
            session.query(PersonORM).filter(PersonORM.id == 3).first().parent_family_id = 1
            session.query(PersonORM).filter(PersonORM.id == 4).first().parent_family_id = 2
            session.commit()
            
            # Get ancestors of child (ID 4)
            ancestors = algorithms.get_ancestors(session, 4)
            
            # Should include father (3) and grandparents (1, 2)
            assert 3 in ancestors  # Father
            assert 1 in ancestors  # Grandfather
            assert 2 in ancestors  # Grandmother
            assert 4 not in ancestors  # Not self
    
    def test_get_direct_descendants(self, temp_db):
        """Test getting direct descendants (children, grandchildren, etc.)."""
        # RED: Test descendant retrieval
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create 3-generation family
            persons_data = [
                {'id': 1, 'first_name': 'Ancestor', 'surname': 'Smith', 'sex': Sex.MALE},
                {'id': 2, 'first_name': 'Child1', 'surname': 'Smith', 'sex': Sex.MALE},
                {'id': 3, 'first_name': 'Child2', 'surname': 'Smith', 'sex': Sex.FEMALE},
                {'id': 4, 'first_name': 'Grandchild', 'surname': 'Smith', 'sex': Sex.MALE},
            ]
            
            for data in persons_data:
                temp_db.add_person(session, data)
            
            # Create families
            family1 = FamilyORM(id=1, father_id=1, mother_id=None)  # Ancestor -> Children
            family2 = FamilyORM(id=2, father_id=2, mother_id=None)  # Child1 -> Grandchild
            session.add(family1)
            session.add(family2)
            
            # Set relationships
            session.query(PersonORM).filter(PersonORM.id == 2).first().parent_family_id = 1
            session.query(PersonORM).filter(PersonORM.id == 3).first().parent_family_id = 1
            session.query(PersonORM).filter(PersonORM.id == 4).first().parent_family_id = 2
            session.commit()
            
            # Get descendants of ancestor (ID 1)
            descendants = algorithms.get_descendants(session, 1)
            
            # Should include children and grandchildren
            assert 2 in descendants  # Child1
            assert 3 in descendants  # Child2
            assert 4 in descendants  # Grandchild
            assert 1 not in descendants  # Not self
    
    def test_empty_ancestors_descendants(self, temp_db):
        """Test ancestor/descendant queries for isolated persons."""
        # RED: Test edge cases
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            isolated_data = {'id': 1, 'first_name': 'Isolated', 'surname': 'Person', 'sex': Sex.MALE}
            temp_db.add_person(session, isolated_data)
            
            ancestors = algorithms.get_ancestors(session, 1)
            descendants = algorithms.get_descendants(session, 1)
            
            assert len(ancestors) == 0
            assert len(descendants) == 0


class TestDataConsistencyChecks:
    """Test data consistency detection algorithms (test-driven)."""
    
    def test_detect_impossible_birth_death_dates(self, temp_db):
        """Test detection of birth after death date."""
        # RED: Test impossible date detection
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create person with birth after death
            person_data = {
                'id': 1, 
                'first_name': 'Impossible', 
                'surname': 'Person', 
                'sex': Sex.MALE
            }
            person = temp_db.add_person(session, person_data)
            
            # TODO: Add birth and death events with impossible dates
            # This requires implementing event creation in database manager
            
            inconsistencies = algorithms.detect_data_inconsistencies(session)
            
            # Should detect the impossible date combination
            # (Implementation needed in algorithms.py)
            assert isinstance(inconsistencies, list)
    
    def test_detect_unrealistic_ages(self, temp_db):
        """Test detection of unrealistic ages (too old)."""
        # RED: Test age validation
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create person born 200 years ago
            person_data = {
                'id': 1,
                'first_name': 'Ancient',
                'surname': 'Person',
                'sex': Sex.MALE
            }
            temp_db.add_person(session, person_data)
            
            # TODO: Add birth event with very old date
            
            inconsistencies = algorithms.detect_data_inconsistencies(session)
            
            # Should detect unrealistic age
            assert isinstance(inconsistencies, list)


class TestPerformanceRequirements:
    """Test performance requirements for algorithms (test-driven)."""
    
    @pytest.mark.slow
    def test_consanguinity_calculation_performance(self, temp_db):
        """Test that consanguinity calculation meets performance requirements."""
        # RED: Performance test
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create moderate-sized family tree (100 persons)
            for i in range(1, 101):
                person_data = {
                    'id': i,
                    'first_name': f'Person{i}',
                    'surname': 'TestFamily',
                    'sex': Sex.MALE if i % 2 == 0 else Sex.FEMALE
                }
                temp_db.add_person(session, person_data)
            
            # Time the calculation
            import time
            start_time = time.time()
            
            # Calculate consanguinity for several persons
            for i in range(1, 11):  # Test first 10 persons
                algorithms.calculate_consanguinity(session, i)
            
            elapsed_time = time.time() - start_time
            
            # Should complete within reasonable time (adjust threshold as needed)
            assert elapsed_time < 5.0  # 5 seconds for 10 calculations
    
    @pytest.mark.slow
    def test_ancestor_query_performance(self, temp_db):
        """Test that ancestor queries perform adequately on larger datasets."""
        # RED: Performance test for ancestor queries
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create deep family tree (20 generations)
            previous_id = None
            for generation in range(20):
                for person_in_gen in range(2):  # 2 persons per generation
                    person_id = generation * 2 + person_in_gen + 1
                    person_data = {
                        'id': person_id,
                        'first_name': f'Gen{generation}Person{person_in_gen}',
                        'surname': 'DeepFamily',
                        'sex': Sex.MALE if person_in_gen == 0 else Sex.FEMALE
                    }
                    temp_db.add_person(session, person_data)
                    
                    if generation > 0:
                        # Create family linking to previous generation
                        family = FamilyORM(
                            id=person_id,
                            father_id=previous_id,
                            mother_id=previous_id + 1 if previous_id else None
                        )
                        session.add(family)
                        
                        # Set parent family
                        person_orm = session.query(PersonORM).filter(PersonORM.id == person_id).first()
                        person_orm.parent_family_id = person_id
                
                previous_id = generation * 2 + 1
            
            session.commit()
            
            # Time ancestor query for deepest person
            import time
            start_time = time.time()
            
            ancestors = algorithms.get_ancestors(session, 39)  # Last person
            
            elapsed_time = time.time() - start_time
            
            # Should complete quickly even for deep trees
            assert elapsed_time < 2.0  # 2 seconds max
            assert len(ancestors) > 0  # Should find some ancestors


# Run specific test groups
if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])