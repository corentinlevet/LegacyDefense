"""
Comprehensive test suite for GeneWeb Python implementation.

This module provides unit tests, integration tests, and performance tests
for all major components of the GeneWeb Python port.
"""
import pytest
import tempfile
import os
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import (
    Person, Family, Event, Date, Place, Name, Sex, EventType, 
    MarriageType, DivorceType, DatePrecision, Calendar
)
from core.database import DatabaseManager, PersonORM, FamilyORM, Base
from core.gedcom import GedcomParser, GedcomExporter
from core.algorithms import GenealogyAlgorithms
from core.templates import TemplateEnvironment, initialize_templates


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


@pytest.fixture
def sample_persons():
    """Create sample persons for testing."""
    # Create a simple family tree
    persons = {}
    
    # Grandparents
    persons[1] = Person(
        id=1,
        name=Name(first_name="John", surname="Smith"),
        sex=Sex.MALE,
        birth=Event(event_type=EventType.BIRTH, date=Date(year=1920))
    )
    
    persons[2] = Person(
        id=2,
        name=Name(first_name="Mary", surname="Jones"),
        sex=Sex.FEMALE,
        birth=Event(event_type=EventType.BIRTH, date=Date(year=1922))
    )
    
    # Parents
    persons[3] = Person(
        id=3,
        name=Name(first_name="Robert", surname="Smith"),
        sex=Sex.MALE,
        birth=Event(event_type=EventType.BIRTH, date=Date(year=1950)),
        parents=1  # Family 1
    )
    
    persons[4] = Person(
        id=4,
        name=Name(first_name="Linda", surname="Brown"),
        sex=Sex.FEMALE,
        birth=Event(event_type=EventType.BIRTH, date=Date(year=1952)),
        parents=2  # Family 2
    )
    
    # Children
    persons[5] = Person(
        id=5,
        name=Name(first_name="David", surname="Smith"),
        sex=Sex.MALE,
        birth=Event(event_type=EventType.BIRTH, date=Date(year=1975)),
        parents=3  # Family 3
    )
    
    persons[6] = Person(
        id=6,
        name=Name(first_name="Sarah", surname="Smith"),
        sex=Sex.FEMALE,
        birth=Event(event_type=EventType.BIRTH, date=Date(year=1978)),
        parents=3  # Family 3
    )
    
    return persons


@pytest.fixture
def sample_families():
    """Create sample families for testing."""
    families = {}
    
    families[1] = Family(
        id=1,
        father=1,
        mother=2,
        children=[3],
        marriage=MarriageType.MARRIED,
        marriage_date=Date(year=1945)
    )
    
    families[2] = Family(
        id=2,
        children=[4]  # Single parent family
    )
    
    families[3] = Family(
        id=3,
        father=3,
        mother=4,
        children=[5, 6],
        marriage=MarriageType.MARRIED,
        marriage_date=Date(year=1970)
    )
    
    return families


class TestModels:
    """Test core data models."""
    
    def test_person_creation(self):
        """Test person creation with all fields."""
        person = Person(
            id=1,
            name=Name(first_name="John", surname="Doe"),
            sex=Sex.MALE,
            birth=Event(
                event_type=EventType.BIRTH,
                date=Date(year=1980, month=5, day=15),
                place=Place(town="New York", country="USA")
            ),
            occupation="Engineer"
        )
        
        assert person.id == 1
        assert person.name.first_name == "John"
        assert person.name.surname == "Doe"
        assert person.sex == Sex.MALE
        assert person.birth.date.year == 1980
        assert person.birth.place.town == "New York"
        assert person.occupation == "Engineer"
    
    def test_date_formatting(self):
        """Test date formatting with various precision levels."""
        # Full date
        date1 = Date(year=1980, month=5, day=15)
        assert str(date1) == "15/05/1980"
        
        # Year and month only
        date2 = Date(year=1980, month=5)
        assert str(date2) == "05/1980"
        
        # Year only
        date3 = Date(year=1980)
        assert str(date3) == "1980"
        
        # With precision
        date4 = Date(year=1980, precision=DatePrecision.ABOUT)
        assert str(date4) == "about 1980"
    
    def test_place_formatting(self):
        """Test place formatting."""
        place = Place(
            place="123 Main St",
            town="New York",
            county="New York County",
            state="New York",
            country="USA"
        )
        
        expected = "123 Main St, New York, New York County, New York, USA"
        assert str(place) == expected
    
    def test_family_relationships(self):
        """Test family relationship structure."""
        family = Family(
            id=1,
            father=10,
            mother=11,
            children=[20, 21, 22],
            marriage=MarriageType.MARRIED,
            marriage_date=Date(year=1990)
        )
        
        assert family.father == 10
        assert family.mother == 11
        assert len(family.children) == 3
        assert 20 in family.children
        assert family.marriage == MarriageType.MARRIED


class TestDatabase:
    """Test database operations."""
    
    def test_database_creation(self, temp_db):
        """Test database table creation."""
        # Database should be created and tables should exist
        with temp_db.get_session() as session:
            # Try to query tables (will fail if they don't exist)
            persons_count = session.query(PersonORM).count()
            families_count = session.query(FamilyORM).count()
            
            assert persons_count == 0
            assert families_count == 0
    
    def test_person_crud(self, temp_db):
        """Test person CRUD operations."""
        with temp_db.get_session() as session:
            # Create
            person_data = {
                'first_name': 'John',
                'surname': 'Doe',
                'sex': Sex.MALE,
                'occupation': 'Engineer'
            }
            person = temp_db.add_person(session, person_data)
            
            assert person.id is not None
            assert person.first_name == 'John'
            assert person.surname == 'Doe'
            
            # Read
            retrieved = session.query(PersonORM).filter(PersonORM.id == person.id).first()
            assert retrieved is not None
            assert retrieved.first_name == 'John'
            
            # Update
            retrieved.occupation = 'Senior Engineer'
            session.commit()
            
            updated = session.query(PersonORM).filter(PersonORM.id == person.id).first()
            assert updated.occupation == 'Senior Engineer'
            
            # Delete
            session.delete(updated)
            session.commit()
            
            deleted = session.query(PersonORM).filter(PersonORM.id == person.id).first()
            assert deleted is None
    
    def test_search_functionality(self, temp_db):
        """Test person search functionality."""
        with temp_db.get_session() as session:
            # Add test persons
            persons_data = [
                {'first_name': 'John', 'surname': 'Smith', 'sex': Sex.MALE},
                {'first_name': 'Jane', 'surname': 'Smith', 'sex': Sex.FEMALE},
                {'first_name': 'Bob', 'surname': 'Johnson', 'sex': Sex.MALE},
                {'first_name': 'Alice', 'surname': 'Brown', 'sex': Sex.FEMALE}
            ]
            
            for data in persons_data:
                temp_db.add_person(session, data)
            
            # Search by surname
            smith_results = temp_db.find_persons_by_name(session, surname='Smith')
            assert len(smith_results) == 2
            
            # Search by first name
            john_results = temp_db.find_persons_by_name(session, first_name='John')
            assert len(john_results) == 1
            assert john_results[0].first_name == 'John'
            
            # General search
            search_results = temp_db.search_persons(session, 'Smith', 10)
            assert len(search_results) == 2
    
    def test_statistics(self, temp_db):
        """Test database statistics."""
        with temp_db.get_session() as session:
            # Add test data
            persons_data = [
                {'first_name': 'John', 'surname': 'Doe', 'sex': Sex.MALE},
                {'first_name': 'Jane', 'surname': 'Doe', 'sex': Sex.FEMALE},
                {'first_name': 'Unknown', 'surname': 'Person', 'sex': Sex.NEUTER}
            ]
            
            for data in persons_data:
                temp_db.add_person(session, data)
            
            # Get statistics
            stats = temp_db.get_statistics(session)
            
            assert stats['total_persons'] == 3
            assert stats['males'] == 1
            assert stats['females'] == 1
            assert stats['unknown_sex'] == 1


class TestGedcomParser:
    """Test GEDCOM import/export functionality."""
    
    def test_gedcom_parsing(self):
        """Test basic GEDCOM parsing."""
        gedcom_content = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
0 @I1@ INDI
1 NAME John /Smith/
2 GIVN John
2 SURN Smith
1 SEX M
1 BIRT
2 DATE 1 JAN 1980
2 PLAC New York, USA
0 @I2@ INDI
1 NAME Jane /Doe/
2 GIVN Jane
2 SURN Doe
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
2 DATE 1 JUN 2000
0 TRLR
"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ged', delete=False) as f:
            f.write(gedcom_content)
            temp_path = f.name
        
        try:
            parser = GedcomParser()
            persons, families = parser.parse_file(temp_path)
            
            assert len(persons) == 2
            assert len(families) == 1
            
            # Check person parsing
            person = list(persons.values())[0]
            assert person.name.first_name in ['John', 'Jane']
            assert person.sex in [Sex.MALE, Sex.FEMALE]
            
            # Check family parsing
            family = list(families.values())[0]
            assert family.marriage == MarriageType.MARRIED
            
        finally:
            os.unlink(temp_path)
    
    def test_gedcom_export(self, sample_persons, sample_families):
        """Test GEDCOM export functionality."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ged', delete=False) as f:
            temp_path = f.name
        
        try:
            exporter = GedcomExporter(sample_persons, sample_families)
            exporter.export_to_file(temp_path)
            
            # Verify file was created and has content
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert 'HEAD' in content
                assert 'INDI' in content
                assert 'FAM' in content
                assert 'TRLR' in content
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestAlgorithms:
    """Test genealogical algorithms."""
    
    def test_ancestor_calculation(self, temp_db):
        """Test ancestor calculation algorithm."""
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create test family tree in database
            # This would require proper ORM object creation
            # Simplified test for now
            ancestors = algorithms.get_ancestors(session, 1, max_generations=10)
            assert isinstance(ancestors, set)
    
    def test_consanguinity_calculation(self, temp_db):
        """Test consanguinity calculation."""
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Test with non-existent person
            result = algorithms.calculate_consanguinity(session, 999)
            assert result.consanguinity == 0.0
            assert len(result.relationship_paths) == 0
    
    def test_relationship_detection(self, temp_db):
        """Test relationship type detection."""
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Test same person
            relationship = algorithms.find_relationship_type(session, 1, 1)
            assert relationship == "same person"
            
            # Test non-existent persons
            relationship = algorithms.find_relationship_type(session, 999, 998)
            assert relationship == "unknown"
    
    def test_data_consistency_checks(self, temp_db):
        """Test data consistency detection."""
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Test with empty database
            inconsistencies = algorithms.detect_data_inconsistencies(session)
            assert isinstance(inconsistencies, list)
    
    def test_string_similarity(self, temp_db):
        """Test string similarity algorithm."""
        algorithms = GenealogyAlgorithms(temp_db)
        
        # Test identical strings
        similarity = algorithms._string_similarity("John", "John")
        assert similarity == 1.0
        
        # Test completely different strings
        similarity = algorithms._string_similarity("John", "Mary")
        assert similarity < 0.5
        
        # Test similar strings
        similarity = algorithms._string_similarity("John", "Jon")
        assert 0.5 < similarity < 1.0
        
        # Test empty strings
        similarity = algorithms._string_similarity("", "")
        assert similarity == 0.0


class TestTemplates:
    """Test template system."""
    
    def test_template_environment_creation(self):
        """Test template environment initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = os.path.join(temp_dir, 'templates')
            locale_dir = os.path.join(temp_dir, 'locales')
            
            env = initialize_templates(template_dir, locale_dir)
            
            assert os.path.exists(template_dir)
            assert os.path.exists(locale_dir)
            assert isinstance(env, TemplateEnvironment)
    
    def test_template_filters(self):
        """Test custom template filters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = os.path.join(temp_dir, 'templates')
            locale_dir = os.path.join(temp_dir, 'locales')
            
            env = TemplateEnvironment(template_dir, locale_dir)
            
            # Test date formatting filter
            date_obj = Date(year=1980, month=5, day=15)
            formatted = env.env.filters['date_format'](date_obj, 'full')
            assert '1980' in formatted
            
            # Test person name filter
            person = Person(
                id=1, 
                name=Name(first_name="John", surname="Doe"),
                sex=Sex.MALE
            )
            name = env.env.filters['person_name'](person, 'full')
            assert name == "John Doe"
    
    def test_internationalization(self):
        """Test internationalization functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = os.path.join(temp_dir, 'templates')
            locale_dir = os.path.join(temp_dir, 'locales')
            
            env = initialize_templates(template_dir, locale_dir)
            
            # Test English
            env.set_language('en')
            translation = env.env.globals['_']('genealogy')
            assert translation == 'Genealogy'
            
            # Test French
            env.set_language('fr')
            translation = env.env.globals['_']('genealogy')
            assert translation == 'Généalogie'


class TestPerformance:
    """Performance tests for large datasets."""
    
    @pytest.mark.slow
    def test_large_database_performance(self, temp_db):
        """Test performance with large number of persons."""
        import time
        
        with temp_db.get_session() as session:
            # Create many test persons
            start_time = time.time()
            
            for i in range(1000):
                person_data = {
                    'first_name': f'Person{i}',
                    'surname': f'Surname{i % 10}',
                    'sex': Sex.MALE if i % 2 == 0 else Sex.FEMALE
                }
                temp_db.add_person(session, person_data)
            
            creation_time = time.time() - start_time
            assert creation_time < 10.0  # Should create 1000 persons in under 10 seconds
            
            # Test search performance
            start_time = time.time()
            results = temp_db.search_persons(session, 'Surname1', 100)
            search_time = time.time() - start_time
            
            assert search_time < 1.0  # Search should be fast
            assert len(results) > 0
    
    @pytest.mark.slow
    def test_consanguinity_performance(self, temp_db):
        """Test consanguinity calculation performance."""
        algorithms = GenealogyAlgorithms(temp_db)
        
        with temp_db.get_session() as session:
            # Create test family structure
            # This would need proper family relationships
            # Simplified test for now
            
            import time
            start_time = time.time()
            
            # Test multiple consanguinity calculations
            for i in range(100):
                result = algorithms.calculate_consanguinity(session, i + 1)
                # Should handle non-existent persons gracefully
                assert result.consanguinity >= 0.0
            
            calc_time = time.time() - start_time
            assert calc_time < 5.0  # Should calculate 100 in under 5 seconds


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_gedcom_import_workflow(self, temp_db):
        """Test complete GEDCOM import workflow."""
        # Create sample GEDCOM
        gedcom_content = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
1 BIRT
2 DATE 1 JAN 1950
0 @I2@ INDI
1 NAME Mary /Jones/
1 SEX F
1 BIRT
2 DATE 15 MAR 1952
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
2 DATE 1 JUN 1970
0 TRLR
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ged', delete=False) as f:
            f.write(gedcom_content)
            temp_path = f.name
        
        try:
            # Parse GEDCOM
            parser = GedcomParser()
            persons, families = parser.parse_file(temp_path)
            
            # Verify parsing
            assert len(persons) == 2
            assert len(families) == 1
            
            # TODO: Import to database
            # This would require converting dataclasses to ORM objects
            
        finally:
            os.unlink(temp_path)
    
    def test_api_database_integration(self, temp_db):
        """Test API endpoints with real database."""
        # This would require setting up the FastAPI test client
        # and testing actual API endpoints
        pass


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")


# Test fixtures for different scenarios
@pytest.fixture
def complex_family_tree(temp_db):
    """Create a complex family tree for testing."""
    # This would create a multi-generation family tree
    # with various relationship types
    pass


@pytest.fixture
def gedcom_sample_file():
    """Create a sample GEDCOM file for testing."""
    content = """0 HEAD
1 SOUR GeneWeb Python Test
1 GEDC
2 VERS 5.5.1
0 @I1@ INDI
1 NAME Test /Person/
1 SEX M
0 TRLR
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ged', delete=False) as f:
        f.write(content)
        yield f.name
    
    os.unlink(f.name)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])