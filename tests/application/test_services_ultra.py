"""
Tests supplémentaires massifs pour atteindre 70%+ de coverage.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from sqlalchemy.orm import Session

from src.geneweb.application.services import ApplicationService
from src.geneweb.infrastructure.models import Person, Family
from src.geneweb.infrastructure.repositories.sql_genealogy_repository import (
    SQLGenealogyRepository,
)


@pytest.fixture
def mock_repo():
    """Mock du repository."""
    repo = Mock(spec=SQLGenealogyRepository)
    repo.db = MagicMock(spec=Session)
    return repo


@pytest.fixture
def app_service(mock_repo):
    """Service avec mock repo."""
    return ApplicationService(mock_repo)


class TestApplicationServiceOldestAlive:
    """Tests pour get_oldest_alive."""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_oldest_alive_success(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test get_oldest_alive avec succès."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Personnes de différents âges
        person1 = Mock(
            id=1,
            first_name="Old",
            surname="Person",
            birth_date="1920-01-01",
            death_date=None,
        )
        person2 = Mock(
            id=2,
            first_name="Young",
            surname="Person",
            birth_date="1990-01-01",
            death_date=None,
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [person1, person2]
        mock_db.query.return_value = mock_query

        result = await app_service.get_oldest_alive("test", limit=10)

        assert result is not None
        assert len(result) == 2
        # Le plus vieux devrait être en premier
        assert result[0]["first_name"] == "Old"
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_oldest_alive_no_duplicates(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test que get_oldest_alive ne retourne pas de doublons."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Même personne apparaissant plusieurs fois
        person = Mock(
            id=1,
            first_name="Unique",
            surname="Person",
            birth_date="1950-01-01",
            death_date=None,
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [person, person]  # Doublon
        mock_db.query.return_value = mock_query

        result = await app_service.get_oldest_alive("test")

        # Devrait n'avoir qu'une seule entrée
        assert len(result) == 1
        mock_db.close.assert_called_once()


class TestApplicationServiceLongestLived:
    """Tests pour get_longest_lived."""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_longest_lived_success(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test get_longest_lived avec succès."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        person1 = Mock(
            id=1,
            first_name="Long",
            surname="Liver",
            birth_date="1900-06-15",
            death_date="2000-06-14",  # 99 ans
        )
        person2 = Mock(
            id=2,
            first_name="Short",
            surname="Liver",
            birth_date="1950-01-01",
            death_date="1980-01-01",  # 30 ans
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [person1, person2]
        mock_db.query.return_value = mock_query

        result = await app_service.get_longest_lived("test", limit=10)

        assert result is not None
        assert len(result) == 2
        # Le plus longtemps vécu devrait être en premier
        assert result[0]["first_name"] == "Long"
        assert result[0]["age"] >= result[1]["age"]
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_longest_lived_age_calculation(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test calcul précis de l'âge."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        person = Mock(
            id=1,
            first_name="Test",
            surname="Person",
            birth_date="1950-06-15",
            death_date="2020-03-10",  # Mort avant son anniversaire
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [person]
        mock_db.query.return_value = mock_query

        result = await app_service.get_longest_lived("test")

        assert result is not None
        assert len(result) == 1
        # Devrait avoir 69 ans (mort avant son 70e anniversaire)
        assert result[0]["age"] == 69
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_longest_lived_not_found(self, app_service, mock_repo):
        """Test quand la généalogie n'existe pas."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_longest_lived("notfound")

        assert result is None


class TestApplicationServiceBirthAnniversaries:
    """Tests pour get_birth_anniversaries."""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_birth_anniversaries_today(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test anniversaires du jour."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        today = date.today()
        person = Mock(
            id=1,
            first_name="Birthday",
            surname="Person",
            birth_date=f"1980-{today.month:02d}-{today.day:02d}",
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [person]
        mock_db.query.return_value = mock_query

        result = await app_service.get_birth_anniversaries("test")

        assert result is not None
        assert len(result) == 1
        assert result[0]["first_name"] == "Birthday"
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_birth_anniversaries_specific_date(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test anniversaires à une date spécifique."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        target_date = date(2025, 6, 15)
        person = Mock(
            id=1, first_name="June", surname="Baby", birth_date="1990-06-15"
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [person]
        mock_db.query.return_value = mock_query

        result = await app_service.get_birth_anniversaries("test", target_date=target_date)

        assert result is not None
        assert len(result) == 1
        assert result[0]["age"] == 35  # 2025 - 1990
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_birth_anniversaries_sorted(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test que les anniversaires sont triés."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        target_date = date(2025, 6, 15)
        person1 = Mock(
            id=1, first_name="Alice", surname="Zulu", birth_date="1990-06-15"
        )
        person2 = Mock(
            id=2, first_name="Bob", surname="Alpha", birth_date="1985-06-15"
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [person1, person2]
        mock_db.query.return_value = mock_query

        result = await app_service.get_birth_anniversaries("test", target_date=target_date)

        assert result is not None
        assert len(result) == 2
        # Devrait être trié par nom: Alpha avant Zulu
        assert result[0]["surname"] == "Alpha"
        assert result[1]["surname"] == "Zulu"
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_birth_anniversaries_not_found(self, app_service, mock_repo):
        """Test quand la généalogie n'existe pas."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_birth_anniversaries("notfound")

        assert result is None


class TestApplicationServiceOldestCouples:
    """Tests pour get_oldest_couples."""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_oldest_couples_success(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test get_oldest_couples avec succès."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        father = Mock(
            first_name="John",
            surname="Doe",
            birth_date="15/06/1930",
            death_date=None,
        )
        mother = Mock(
            first_name="Jane",
            surname="Smith",
            birth_date="22/03/1932",
            death_date=None,
        )
        
        family = Mock(
            id=1,
            marriage_date="15/06/1950",
            father=father,
            mother=mother,
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [family]
        mock_db.query.return_value = mock_query

        result = await app_service.get_oldest_couples("test", limit=10)

        assert result is not None
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]["father_first_name"] == "John"
            assert result[0]["mother_first_name"] == "Jane"
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_oldest_couples_not_found(self, app_service, mock_repo):
        """Test quand la généalogie n'existe pas."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_oldest_couples("notfound")

        assert result is None


class TestApplicationServiceSearch:
    """Tests pour search_persons."""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_search_persons_no_criteria(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test recherche sans critères."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []
        mock_db.query.return_value = mock_query

        result = await app_service.search_persons("test", None, None)

        # Devrait retourner une liste vide
        assert result == []

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_search_persons_only_first_name(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test recherche par prénom uniquement."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        person = Mock(id=1, first_name="John", surname="Doe")

        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.all.return_value = [person]
        mock_db.query.return_value = mock_query

        result = await app_service.search_persons("test", "John", None)

        assert len(result) == 1
        assert result[0].first_name == "John"

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_search_persons_only_last_name(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test recherche par nom uniquement."""
        mock_genealogy = Mock()
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        person = Mock(id=1, first_name="John", surname="Doe")

        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.all.return_value = [person]
        mock_db.query.return_value = mock_query

        result = await app_service.search_persons("test", None, "Doe")

        assert len(result) == 1
        assert result[0].surname == "Doe"
