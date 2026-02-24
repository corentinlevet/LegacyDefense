"""
Tests complémentaires pour ApplicationService (services.py).
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from src.geneweb.application.services import (
    ApplicationService,
    GenealogyService,
    _format_date_for_gedcom,
    is_possibly_alive,
    parse_date_for_sorting,
)
from src.geneweb.infrastructure.models import Family, Genealogy, Person
from src.geneweb.infrastructure.repositories.sql_genealogy_repository import (
    SQLGenealogyRepository,
)


@pytest.fixture
def mock_repo():
    """Mock du repository de généalogie."""
    return Mock(spec=SQLGenealogyRepository)


@pytest.fixture
def app_service(mock_repo):
    """Instance du service d'application avec un mock repo."""
    return ApplicationService(mock_repo)


@pytest.fixture
def mock_db():
    """Mock de la session de base de données."""
    return MagicMock(spec=Session)


class TestApplicationServiceAdvanced:
    """Tests avancés pour ApplicationService."""

    @pytest.mark.asyncio
    async def test_search_persons_genealogy_not_found(self, app_service, mock_repo):
        """Test search_persons quand la généalogie n'existe pas."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.search_persons("nonexistent", "John", "Doe")
        assert result == []


class TestGenealogyService:
    """Tests pour GenealogyService."""

    @patch("src.geneweb.application.services.SessionLocal")
    def test_create_genealogy_new(self, mock_session_local):
        """Test de création d'une nouvelle généalogie."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None  # Pas de généalogie existante
        mock_db.query.return_value = mock_query

        service = GenealogyService()
        result = service.create_genealogy("new_genealogy")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("src.geneweb.application.services.SessionLocal")
    def test_create_genealogy_existing_without_force(self, mock_session_local):
        """Test de création d'une généalogie existante sans force."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        existing_genealogy = Mock(spec=Genealogy)
        existing_genealogy.name = "existing"

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = existing_genealogy
        mock_db.query.return_value = mock_query

        service = GenealogyService()
        with patch("builtins.print") as mock_print:
            result = service.create_genealogy("existing", force=False)
            mock_print.assert_called()
            mock_db.delete.assert_not_called()

    @patch("src.geneweb.application.services.SessionLocal")
    def test_create_genealogy_existing_with_force(self, mock_session_local):
        """Test de création d'une généalogie existante avec force."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        existing_genealogy = Mock(spec=Genealogy)
        existing_genealogy.name = "existing"

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        # Première fois retourne la généalogie existante, deuxième fois None
        mock_filter.first.side_effect = [existing_genealogy]
        mock_db.query.return_value = mock_query

        service = GenealogyService()
        with patch("builtins.print") as mock_print:
            result = service.create_genealogy("existing", force=True)
            mock_db.delete.assert_called_once_with(existing_genealogy)
            assert mock_db.commit.call_count == 2  # Une fois pour delete, une pour add

    @patch("src.geneweb.application.services.SessionLocal")
    def test_get_all_genealogies(self, mock_session_local):
        """Test de récupération de toutes les généalogies."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_genealogies = [
            Mock(name="gen1"),
            Mock(name="gen2"),
            Mock(name="gen3"),
        ]

        mock_query = Mock()
        mock_query.all.return_value = mock_genealogies
        mock_db.query.return_value = mock_query

        service = GenealogyService()
        result = service.get_all_genealogies()

        assert len(result) == 3
        assert result == mock_genealogies
        mock_db.close.assert_called_once()

    @patch("src.geneweb.application.services.SessionLocal")
    def test_get_all_genealogies_empty(self, mock_session_local):
        """Test de récupération quand il n'y a pas de généalogies."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_query = Mock()
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = GenealogyService()
        result = service.get_all_genealogies()

        assert len(result) == 0
        mock_db.close.assert_called_once()


class TestParseDateForSortingExtended:
    """Tests étendus pour parse_date_for_sorting."""

    def test_parse_date_with_slashes(self):
        """Test avec format DD/MM/YYYY."""
        result = parse_date_for_sorting("15/06/1980")
        assert result == (1980, 6, 15)

    def test_parse_date_with_iso(self):
        """Test avec format ISO YYYY-MM-DD."""
        result = parse_date_for_sorting("1980-06-15")
        assert result == (1980, 6, 15)

    def test_parse_date_invalid_returns_default(self):
        """Test que les dates invalides retournent (9999, 12, 31)."""
        result = parse_date_for_sorting("invalid date")
        assert result == (9999, 12, 31)

    def test_parse_date_partial_month_year(self):
        """Test avec mois et année seulement."""
        result = parse_date_for_sorting("JUN 1980")
        # La fonction actuelle ne parse pas les noms de mois, elle extrait juste l'année
        assert result == (1980, 1, 1)

    def test_parse_date_year_extraction(self):
        """Test d'extraction de l'année depuis un texte."""
        result = parse_date_for_sorting("Né en 1980")
        assert result[0] == 1980


class TestFormatDateForGedcomExtended:
    """Tests étendus pour _format_date_for_gedcom."""

    def test_format_date_datetime_object(self):
        """Test avec un objet datetime."""
        dt = datetime(1980, 6, 15)
        result = _format_date_for_gedcom(dt)
        assert result == "15 JUN 1980"

    def test_format_date_string_slash(self):
        """Test avec une chaîne au format DD/MM/YYYY."""
        result = _format_date_for_gedcom("15/06/1980")
        # La fonction retourne la chaîne telle quelle si ce n'est pas un datetime
        assert result == "15/06/1980"

    def test_format_date_string_iso(self):
        """Test avec une chaîne au format ISO."""
        result = _format_date_for_gedcom("1980-06-15")
        # La fonction retourne la chaîne telle quelle si ce n'est pas un datetime
        assert result == "1980-06-15"

    def test_format_date_all_months(self):
        """Test de tous les mois."""
        months = [
            "JAN",
            "FEB",
            "MAR",
            "APR",
            "MAY",
            "JUN",
            "JUL",
            "AUG",
            "SEP",
            "OCT",
            "NOV",
            "DEC",
        ]
        for i, month in enumerate(months, 1):
            dt = datetime(2000, i, 15)
            result = _format_date_for_gedcom(dt)
            assert result == f"15 {month} 2000"
