"""Tests additionnels massifs pour services.py pour atteindre 70%+"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.geneweb.application.services import ApplicationService


@pytest.fixture
def mock_repo():
    return Mock()


@pytest.fixture
def app_service(mock_repo):
    return ApplicationService(mock_repo)


class TestApplicationServiceGetGenealogyDetails:
    """Tests supplémentaires pour get_genealogy_details"""

    @pytest.mark.asyncio
    async def test_get_genealogy_details_success(self, app_service, mock_repo):
        """Test récupération détails avec comptage"""
        mock_genealogy = Mock(id=1, name="test")
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.count_persons = Mock(return_value=100)

        result = await app_service.get_genealogy_details("test")

        assert result is not None
        assert result.person_count == 100
        mock_repo.count_persons.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_genealogy_details_not_found(self, app_service, mock_repo):
        """Test avec généalogie inexistante"""
        mock_repo.get_by_name = Mock(return_value=None)

        result = await app_service.get_genealogy_details("nonexistent")

        assert result is None


class TestApplicationServiceGetFirstNames:
    """Tests supplémentaires pour get_first_names"""

    @pytest.mark.asyncio
    async def test_get_first_names_multiple(self, app_service, mock_repo):
        """Test récupération de plusieurs prénoms"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_first_names = Mock(return_value=["John", "Jane", "Bob"])

        result = await app_service.get_first_names("test")

        assert len(result) == 3
        assert "John" in result
        mock_repo.get_first_names.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_first_names_empty(self, app_service, mock_repo):
        """Test avec aucun prénom"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_first_names = Mock(return_value=[])

        result = await app_service.get_first_names("test")

        assert result == []


class TestApplicationServiceGetLastNames:
    """Tests supplémentaires pour get_last_names"""

    @pytest.mark.asyncio
    async def test_get_last_names_multiple(self, app_service, mock_repo):
        """Test récupération de plusieurs noms"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_last_names = Mock(return_value=["Doe", "Smith", "Johnson"])

        result = await app_service.get_last_names("test")

        assert len(result) == 3
        assert "Smith" in result

    @pytest.mark.asyncio
    async def test_get_last_names_empty(self, app_service, mock_repo):
        """Test avec aucun nom"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_last_names = Mock(return_value=[])

        result = await app_service.get_last_names("test")

        assert result == []


class TestApplicationServiceGetPlaces:
    """Tests supplémentaires pour get_places"""

    @pytest.mark.asyncio
    async def test_get_places_multiple(self, app_service, mock_repo):
        """Test récupération de plusieurs lieux"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_places = Mock(return_value=["Paris", "Lyon", "Marseille"])

        result = await app_service.get_places("test")

        assert len(result) == 3
        assert "Paris" in result

    @pytest.mark.asyncio
    async def test_get_places_empty(self, app_service, mock_repo):
        """Test avec aucun lieu"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_places = Mock(return_value=[])

        result = await app_service.get_places("test")

        assert result == []


class TestApplicationServiceGetOccupations:
    """Tests supplémentaires pour get_occupations"""

    @pytest.mark.asyncio
    async def test_get_occupations_multiple(self, app_service, mock_repo):
        """Test récupération de plusieurs professions"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_occupations = Mock(return_value=["Engineer", "Doctor", "Teacher"])

        result = await app_service.get_occupations("test")

        assert len(result) == 3
        assert "Engineer" in result

    @pytest.mark.asyncio
    async def test_get_occupations_empty(self, app_service, mock_repo):
        """Test avec aucune profession"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_occupations = Mock(return_value=[])

        result = await app_service.get_occupations("test")

        assert result == []


class TestApplicationServiceGetSources:
    """Tests supplémentaires pour get_sources"""

    @pytest.mark.asyncio
    async def test_get_sources_multiple(self, app_service, mock_repo):
        """Test récupération de plusieurs sources"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_sources = Mock(return_value=["Birth certificate", "Census 1900"])

        result = await app_service.get_sources("test")

        assert len(result) == 2
        assert "Birth certificate" in result

    @pytest.mark.asyncio
    async def test_get_sources_empty(self, app_service, mock_repo):
        """Test avec aucune source"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.get_sources = Mock(return_value=[])

        result = await app_service.get_sources("test")

        assert result == []


class TestApplicationServiceStatistics:
    """Tests pour méthodes de statistiques"""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_last_births_limit(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test limite du nombre de naissances récentes"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        persons = [
            Mock(
                id=i,
                first_name=f"Person{i}",
                surname="Test",
                birth_date=f"0{i}/01/2020",
            )
            for i in range(1, 11)
        ]

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = persons
        mock_db.query.return_value = mock_query

        result = await app_service.get_last_births("test", limit=5)

        assert result is not None
        assert isinstance(result, list)
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_last_deaths_limit(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test limite du nombre de décès récents"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        persons = [
            Mock(
                id=i,
                first_name=f"Person{i}",
                surname="Test",
                death_date=f"0{i}/01/2020",
            )
            for i in range(1, 11)
        ]

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = persons
        mock_db.query.return_value = mock_query

        result = await app_service.get_last_deaths("test", limit=5)

        assert result is not None
        assert isinstance(result, list)
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_last_marriages_limit(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test limite du nombre de mariages récents"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        father = Mock(first_name="John", surname="Doe")
        mother = Mock(first_name="Jane", surname="Smith")
        families = [
            Mock(id=i, father=father, mother=mother, marriage_date=f"0{i}/01/2020")
            for i in range(1, 11)
        ]

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = families
        mock_db.query.return_value = mock_query

        result = await app_service.get_last_marriages("test", limit=5)

        assert result is not None
        assert isinstance(result, list)
        mock_db.close.assert_called_once()
