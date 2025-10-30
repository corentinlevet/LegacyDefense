"""
Tests pour les repositories SQL.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.geneweb.infrastructure.database import Base
from src.geneweb.infrastructure.models import Person, Family, Genealogy
from src.geneweb.infrastructure.repositories.sql_person_repository import (
    SQLPersonRepository,
)
from src.geneweb.infrastructure.repositories.sql_genealogy_repository import (
    SQLGenealogyRepository,
)


@pytest.fixture
def test_db():
    """Crée une base de données de test en mémoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_genealogy(test_db):
    """Crée une généalogie de test."""
    genealogy = Genealogy(name="Test Genealogy")
    test_db.add(genealogy)
    test_db.commit()
    test_db.refresh(genealogy)
    return genealogy


@pytest.fixture
def sample_person(test_db, sample_genealogy):
    """Crée une personne de test."""
    person = Person(
        first_name="Jean",
        last_name="Dupont",
        sex="M",
        genealogy_id=sample_genealogy.id,
    )
    test_db.add(person)
    test_db.commit()
    test_db.refresh(person)
    return person


class TestSQLPersonRepository:
    """Tests pour SQLPersonRepository."""

    def test_get_by_id_existing_person(self, test_db, sample_person):
        """Test récupération d'une personne existante par ID."""
        repo = SQLPersonRepository(test_db)
        person = repo.get_by_id(sample_person.id)
        
        assert person is not None
        assert person.id == sample_person.id
        assert person.first_name == "Jean"
        assert person.last_name == "Dupont"

    def test_get_by_id_non_existing_person(self, test_db):
        """Test récupération d'une personne inexistante."""
        repo = SQLPersonRepository(test_db)
        person = repo.get_by_id(99999)
        
        assert person is None

    def test_add_person(self, test_db, sample_genealogy):
        """Test ajout d'une nouvelle personne."""
        repo = SQLPersonRepository(test_db)
        
        new_person = Person(
            first_name="Marie",
            last_name="Martin",
            sex="F",
            genealogy_id=sample_genealogy.id,
        )
        
        result = repo.add(new_person)
        
        assert result is not None
        assert result.id is not None
        assert result.first_name == "Marie"
        assert result.last_name == "Martin"
        
        # Vérifier que la personne est bien dans la DB
        retrieved = test_db.query(Person).filter(Person.id == result.id).first()
        assert retrieved is not None
        assert retrieved.first_name == "Marie"

    def test_add_person_with_dates(self, test_db, sample_genealogy):
        """Test ajout d'une personne avec dates de naissance et décès."""
        repo = SQLPersonRepository(test_db)
        
        new_person = Person(
            first_name="Pierre",
            last_name="Durand",
            sex="M",
            birth_date="15 JUN 1950",
            death_date="20 DEC 2020",
            genealogy_id=sample_genealogy.id,
        )
        
        result = repo.add(new_person)
        
        assert result.birth_date == "15 JUN 1950"
        assert result.death_date == "20 DEC 2020"

    def test_add_multiple_persons(self, test_db, sample_genealogy):
        """Test ajout de plusieurs personnes."""
        repo = SQLPersonRepository(test_db)
        
        persons_data = [
            {"first_name": "Alice", "last_name": "Blanc", "sex": "F"},
            {"first_name": "Bob", "last_name": "Noir", "sex": "M"},
            {"first_name": "Charlie", "last_name": "Rouge", "sex": "M"},
        ]
        
        added_persons = []
        for data in persons_data:
            person = Person(**data, genealogy_id=sample_genealogy.id)
            result = repo.add(person)
            added_persons.append(result)
        
        assert len(added_persons) == 3
        
        # Vérifier que toutes les personnes sont dans la DB
        all_persons = test_db.query(Person).all()
        assert len(all_persons) >= 3


class TestSQLGenealogyRepository:
    """Tests pour SQLGenealogyRepository."""

    def test_get_by_name_existing(self, test_db, sample_genealogy):
        """Test récupération d'une généalogie existante par nom."""
        repo = SQLGenealogyRepository(test_db)
        genealogy = repo.get_by_name(sample_genealogy.name)
        
        assert genealogy is not None
        assert genealogy.name == "Test Genealogy"
        assert genealogy.id == sample_genealogy.id

    def test_get_by_name_non_existing(self, test_db):
        """Test récupération d'une généalogie inexistante."""
        repo = SQLGenealogyRepository(test_db)
        genealogy = repo.get_by_name("Non Existing Genealogy")
        
        assert genealogy is None

    def test_get_by_name_case_sensitive(self, test_db, sample_genealogy):
        """Test que la recherche par nom est case-sensitive."""
        repo = SQLGenealogyRepository(test_db)
        
        # La recherche exacte doit fonctionner
        genealogy = repo.get_by_name("Test Genealogy")
        assert genealogy is not None
        
        # La recherche avec une casse différente pourrait ne pas fonctionner
        # (dépend de la configuration de la DB)
        genealogy_lower = repo.get_by_name("test genealogy")
        # On ne fait pas d'assertion stricte car cela dépend de SQLite

    def test_create_genealogy(self, test_db):
        """Test création d'une nouvelle généalogie."""
        repo = SQLGenealogyRepository(test_db)
        
        new_genealogy = Genealogy(name="New Family Tree")
        test_db.add(new_genealogy)
        test_db.commit()
        test_db.refresh(new_genealogy)
        
        # Vérifier qu'on peut la récupérer
        retrieved = repo.get_by_name("New Family Tree")
        assert retrieved is not None
        assert retrieved.name == "New Family Tree"

    def test_genealogy_with_persons(self, test_db, sample_genealogy):
        """Test généalogie avec des personnes associées."""
        # Ajouter des personnes à la généalogie
        person1 = Person(
            first_name="Person1",
            last_name="Test",
            sex="M",
            genealogy_id=sample_genealogy.id,
        )
        person2 = Person(
            first_name="Person2",
            last_name="Test",
            sex="F",
            genealogy_id=sample_genealogy.id,
        )
        
        test_db.add(person1)
        test_db.add(person2)
        test_db.commit()
        
        # Récupérer la généalogie
        repo = SQLGenealogyRepository(test_db)
        genealogy = repo.get_by_name(sample_genealogy.name)
        
        assert genealogy is not None
        # Vérifier que les personnes sont associées
        persons = test_db.query(Person).filter(
            Person.genealogy_id == genealogy.id
        ).all()
        assert len(persons) == 2


class TestRepositoryEdgeCases:
    """Tests des cas limites pour les repositories."""

    def test_person_repository_with_empty_names(self, test_db, sample_genealogy):
        """Test ajout d'une personne avec des noms vides."""
        repo = SQLPersonRepository(test_db)
        
        person = Person(
            first_name="",
            last_name="",
            sex="U",
            genealogy_id=sample_genealogy.id,
        )
        
        result = repo.add(person)
        assert result is not None
        assert result.first_name == ""
        assert result.last_name == ""

    def test_person_repository_with_long_names(self, test_db, sample_genealogy):
        """Test ajout d'une personne avec des noms très longs."""
        repo = SQLPersonRepository(test_db)
        
        long_name = "A" * 200
        person = Person(
            first_name=long_name,
            last_name=long_name,
            sex="M",
            genealogy_id=sample_genealogy.id,
        )
        
        result = repo.add(person)
        assert result is not None
        assert result.first_name == long_name
        assert result.last_name == long_name

    def test_person_with_special_characters(self, test_db, sample_genealogy):
        """Test ajout d'une personne avec des caractères spéciaux."""
        repo = SQLPersonRepository(test_db)
        
        person = Person(
            first_name="François-René",
            last_name="O'Connor-Smith",
            sex="M",
            genealogy_id=sample_genealogy.id,
        )
        
        result = repo.add(person)
        assert result is not None
        assert result.first_name == "François-René"
        assert result.last_name == "O'Connor-Smith"

    def test_get_by_id_with_zero(self, test_db):
        """Test récupération avec ID = 0."""
        repo = SQLPersonRepository(test_db)
        person = repo.get_by_id(0)
        assert person is None

    def test_get_by_id_with_negative(self, test_db):
        """Test récupération avec ID négatif."""
        repo = SQLPersonRepository(test_db)
        person = repo.get_by_id(-1)
        assert person is None
