"""
Tests pour les repositories SQL.
"""

import pytest
from unittest.mock import MagicMock, Mock, call
from sqlalchemy.orm import Session

from src.geneweb.infrastructure.repositories.sql_genealogy_repository import (
    SQLGenealogyRepository,
)
from src.geneweb.infrastructure.repositories.sql_person_repository import (
    SQLPersonRepository,
)
from src.geneweb.infrastructure.models import Genealogy, Person, Family, Event


@pytest.fixture
def mock_db():
    """Mock de la session de base de données."""
    return MagicMock(spec=Session)


class TestSQLGenealogyRepository:
    """Tests pour SQLGenealogyRepository."""

    def test_init(self, mock_db):
        """Test de l'initialisation du repository."""
        repo = SQLGenealogyRepository(mock_db)
        assert repo.db == mock_db

    def test_get_by_name_found(self, mock_db):
        """Test get_by_name quand la généalogie existe."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.name = "test"

        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = mock_genealogy
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_by_name("test")

        assert result == mock_genealogy
        mock_db.execute.assert_called_once()

    def test_get_by_name_not_found(self, mock_db):
        """Test get_by_name quand la généalogie n'existe pas."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_by_name("nonexistent")

        assert result is None

    def test_count_persons(self, mock_db):
        """Test count_persons."""
        mock_result = Mock()
        mock_result.scalar_one.return_value = 42
        mock_db.execute.return_value = mock_result

        repo = SQLGenealogyRepository(mock_db)
        result = repo.count_persons(1)

        assert result == 42
        mock_db.execute.assert_called_once()

    def test_count_persons_zero(self, mock_db):
        """Test count_persons quand il n'y a pas de personnes."""
        mock_result = Mock()
        mock_result.scalar_one.return_value = None
        mock_db.execute.return_value = mock_result

        repo = SQLGenealogyRepository(mock_db)
        result = repo.count_persons(1)

        assert result == 0

    def test_get_first_names(self, mock_db):
        """Test get_first_names."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = ["Alice", "Bob", "Charlie"]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_first_names(1)

        assert result == ["Alice", "Bob", "Charlie"]
        mock_db.execute.assert_called_once()

    def test_get_first_names_empty(self, mock_db):
        """Test get_first_names quand il n'y a pas de prénoms."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_first_names(1)

        assert result == []

    def test_get_last_names(self, mock_db):
        """Test get_last_names."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = ["Smith", "Johnson", "Brown"]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_last_names(1)

        assert result == ["Smith", "Johnson", "Brown"]
        mock_db.execute.assert_called_once()

    def test_get_places(self, mock_db):
        """Test get_places avec différentes sources de lieux."""
        # Simuler les résultats de différentes requêtes
        mock_results = [
            Mock(scalars=lambda: Mock(all=lambda: ["Paris", "Lyon"])),  # birth_place
            Mock(scalars=lambda: Mock(all=lambda: ["Paris", "Marseille"])),  # death_place
            Mock(scalars=lambda: Mock(all=lambda: ["Lyon"])),  # baptism_place
            Mock(scalars=lambda: Mock(all=lambda: ["Nice"])),  # burial_place
            Mock(scalars=lambda: Mock(all=lambda: ["Bordeaux"])),  # marriage_place
        ]

        mock_db.execute.side_effect = mock_results

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_places(1)

        # Devrait retourner tous les lieux uniques triés
        assert sorted(result) == ["Bordeaux", "Lyon", "Marseille", "Nice", "Paris"]
        assert mock_db.execute.call_count == 5

    def test_get_places_empty(self, mock_db):
        """Test get_places quand il n'y a pas de lieux."""
        mock_results = [
            Mock(scalars=lambda: Mock(all=lambda: [])),
            Mock(scalars=lambda: Mock(all=lambda: [])),
            Mock(scalars=lambda: Mock(all=lambda: [])),
            Mock(scalars=lambda: Mock(all=lambda: [])),
            Mock(scalars=lambda: Mock(all=lambda: [])),
        ]

        mock_db.execute.side_effect = mock_results

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_places(1)

        assert result == []

    def test_get_occupations(self, mock_db):
        """Test get_occupations."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = ["Engineer", "Doctor", "Teacher"]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_occupations(1)

        assert result == ["Engineer", "Doctor", "Teacher"]
        mock_db.execute.assert_called_once()

    def test_get_occupations_empty(self, mock_db):
        """Test get_occupations quand il n'y a pas de professions."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_occupations(1)

        assert result == []

    def test_get_sources(self, mock_db):
        """Test get_sources avec sources d'événements et de familles."""
        mock_results = [
            Mock(scalars=lambda: Mock(all=lambda: ["Source1", "Source2"])),  # events
            Mock(scalars=lambda: Mock(all=lambda: ["Source2", "Source3"])),  # families
        ]

        mock_db.execute.side_effect = mock_results

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_sources(1)

        # Devrait retourner toutes les sources uniques triées
        assert sorted(result) == ["Source1", "Source2", "Source3"]
        assert mock_db.execute.call_count == 2

    def test_get_sources_empty(self, mock_db):
        """Test get_sources quand il n'y a pas de sources."""
        mock_results = [
            Mock(scalars=lambda: Mock(all=lambda: [])),
            Mock(scalars=lambda: Mock(all=lambda: [])),
        ]

        mock_db.execute.side_effect = mock_results

        repo = SQLGenealogyRepository(mock_db)
        result = repo.get_sources(1)

        assert result == []


class TestSQLPersonRepository:
    """Tests pour SQLPersonRepository."""

    def test_init(self, mock_db):
        """Test de l'initialisation du repository."""
        repo = SQLPersonRepository(mock_db)
        assert repo.db_session == mock_db

    def test_get_by_id_found(self, mock_db):
        """Test get_by_id quand la personne existe."""
        mock_person = Mock(spec=Person)
        mock_person.id = 1

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_person
        mock_db.query.return_value = mock_query

        repo = SQLPersonRepository(mock_db)
        result = repo.get_by_id(1)

        assert result == mock_person
        mock_db.query.assert_called_once_with(Person)

    def test_get_by_id_not_found(self, mock_db):
        """Test get_by_id quand la personne n'existe pas."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query

        repo = SQLPersonRepository(mock_db)
        result = repo.get_by_id(999)

        assert result is None

    def test_add_person(self, mock_db):
        """Test add avec une nouvelle personne."""
        mock_person = Mock(spec=Person)
        mock_person.id = None
        mock_person.first_name = "John"
        mock_person.surname = "Doe"

        repo = SQLPersonRepository(mock_db)
        result = repo.add(mock_person)

        mock_db.add.assert_called_once_with(mock_person)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_person)
        assert result == mock_person

    def test_add_person_multiple(self, mock_db):
        """Test d'ajout de plusieurs personnes."""
        mock_person1 = Mock(spec=Person)
        mock_person2 = Mock(spec=Person)

        repo = SQLPersonRepository(mock_db)
        result1 = repo.add(mock_person1)
        result2 = repo.add(mock_person2)

        assert mock_db.add.call_count == 2
        assert mock_db.commit.call_count == 2
        assert result1 == mock_person1
        assert result2 == mock_person2
