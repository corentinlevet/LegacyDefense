"""Tests mega pour pousser le coverage de services.py vers 60%+"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.geneweb.application.services import ApplicationService, GenealogyService


@pytest.fixture
def mock_repo():
    repo = Mock()
    return repo


@pytest.fixture
def app_service(mock_repo):
    return ApplicationService(mock_repo)


class TestApplicationServiceDeathAnniversaries:
    """Tests pour get_death_anniversaries"""

    @pytest.mark.asyncio
    async def test_get_death_anniversaries_not_found(self, app_service, mock_repo):
        """Test quand la généalogie n'existe pas"""
        mock_repo.get_by_name = Mock(return_value=None)
        app_service.genealogy_repo = mock_repo

        result = await app_service.get_death_anniversaries("notfound")

        assert result is None


class TestApplicationServicePlacesSurnames:
    """Tests pour get_places_surnames"""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_places_surnames_success(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test récupération lieux et noms"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        app_service.genealogy_repo = mock_repo

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        person = Mock(
            id=1,
            surname="Doe",
            birth_place="Paris",
            death_place="Lyon",
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [person]
        mock_db.query.return_value = mock_query

        result = await app_service.get_places_surnames("test")

        assert isinstance(result, list)
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_places_surnames_not_found(self, app_service, mock_repo):
        """Test quand la généalogie n'existe pas"""
        mock_repo.get_by_name = Mock(return_value=None)
        app_service.genealogy_repo = mock_repo

        result = await app_service.get_places_surnames("notfound")

        assert result == []


class TestApplicationServiceAddFamily:
    """Tests pour add_family"""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_add_family_success(self, mock_session_local, app_service, mock_repo):
        """Test ajout d'une famille réussi"""
        mock_genealogy = Mock(id=1)
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        app_service.genealogy_repo = mock_repo

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        form_data = {
            "pa1_fn": "John",
            "pa1_sn": "Doe",
            "pa2_fn": "Jane",
            "pa2_sn": "Smith",
        }

        result = await app_service.add_family("test", form_data)

        # Result can be None or family ID
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()


class TestApplicationServiceGetFamily:
    """Tests pour get_family"""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_family_success(self, mock_session_local, app_service):
        """Test récupération d'une famille réussie"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        father = Mock(first_name="John")
        mother = Mock(first_name="Jane")
        family = Mock(id=1, father=father, mother=mother)

        mock_query = Mock()
        mock_options = Mock()
        mock_filter = Mock()
        mock_query.options.return_value = mock_options
        mock_options.filter.return_value = mock_filter
        mock_filter.first.return_value = family
        mock_db.query.return_value = mock_query

        result = await app_service.get_family(1)

        assert result is not None
        assert result.id == 1
        mock_db.close.assert_called_once()


class TestApplicationServiceGetPersonDetails:
    """Tests pour get_person_details"""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_person_details_success(self, mock_session_local, app_service):
        """Test récupération détails personne réussie"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        person = Mock(id=1, first_name="John", surname="Doe")

        mock_query = Mock()
        mock_options = Mock()
        mock_filter = Mock()
        mock_query.options.return_value = mock_options
        mock_options.filter.return_value = mock_filter
        mock_filter.first.return_value = person
        mock_db.query.return_value = mock_query

        result = await app_service.get_person_details(1)

        assert result is not None
        assert result.id == 1
        mock_db.close.assert_called_once()


class TestApplicationServiceRenameGenealogy:
    """Tests pour rename_genealogy"""

    @pytest.mark.asyncio
    async def test_rename_genealogy_success(self, app_service, mock_repo):
        """Test renommage généalogie réussi"""
        mock_genealogy = Mock(id=1, name="old_name")
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.update = Mock(return_value=None)
        mock_repo.count_persons = Mock(return_value=10)
        app_service.genealogy_repo = mock_repo

        result = await app_service.rename_genealogy("old_name", "new_name")

        assert result is not None
        assert result.name == "new_name"
        assert result.person_count == 10
        mock_repo.update.assert_called_once_with(mock_genealogy)

    @pytest.mark.asyncio
    async def test_rename_genealogy_not_found(self, app_service, mock_repo):
        """Test renommage généalogie inexistante"""
        mock_repo.get_by_name = Mock(return_value=None)
        app_service.genealogy_repo = mock_repo

        result = await app_service.rename_genealogy("nonexistent", "new_name")

        assert result is None


class TestApplicationServiceDeleteGenealogy:
    """Tests pour delete_genealogy"""

    @pytest.mark.asyncio
    async def test_delete_genealogy_success(self, app_service, mock_repo):
        """Test suppression généalogie réussie"""
        mock_genealogy = Mock(id=1, name="test")
        mock_repo.get_by_name = Mock(return_value=mock_genealogy)
        mock_repo.delete = Mock(return_value=None)
        app_service.genealogy_repo = mock_repo

        result = await app_service.delete_genealogy("test")

        assert result is True
        mock_repo.delete.assert_called_once_with(mock_genealogy)

    @pytest.mark.asyncio
    async def test_delete_genealogy_not_found(self, app_service, mock_repo):
        """Test suppression généalogie inexistante"""
        mock_repo.get_by_name = Mock(return_value=None)
        app_service.genealogy_repo = mock_repo

        result = await app_service.delete_genealogy("nonexistent")

        assert result is False
