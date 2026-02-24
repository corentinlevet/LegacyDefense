"""
Tests massifs pour services.py pour atteindre 70%+ de coverage.
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest
from sqlalchemy.orm import Session

from src.geneweb.application.services import (
    ApplicationService,
    GenealogyService,
    is_possibly_alive,
    parse_date_for_sorting,
)
from src.geneweb.infrastructure.models import Event, Family, Genealogy, Person
from src.geneweb.infrastructure.repositories.sql_genealogy_repository import (
    SQLGenealogyRepository,
)


@pytest.fixture
def mock_session():
    """Mock de session SQLAlchemy."""
    return MagicMock(spec=Session)


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


class TestApplicationServiceMethods:
    """Tests des méthodes principales d'ApplicationService."""

    @pytest.mark.asyncio
    async def test_get_genealogy_details_success(self, app_service, mock_repo):
        """Test get_genealogy_details avec succès."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_genealogy.name = "Test"
        mock_repo.get_by_name.return_value = mock_genealogy
        mock_repo.count_persons.return_value = 100

        result = await app_service.get_genealogy_details("Test")

        # La méthode retourne un objet avec attribut person_count, pas un dict
        assert result.person_count == 100
        mock_repo.get_by_name.assert_called_once_with("Test")
        mock_repo.count_persons.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_genealogy_details_not_found(self, app_service, mock_repo):
        """Test get_genealogy_details quand non trouvé."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_genealogy_details("NotFound")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_first_names_success(self, app_service, mock_repo):
        """Test get_first_names avec succès."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy
        mock_repo.get_first_names.return_value = ["Alice", "Bob", "Charlie"]

        result = await app_service.get_first_names("Test")

        assert result == ["Alice", "Bob", "Charlie"]
        mock_repo.get_first_names.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_first_names_not_found(self, app_service, mock_repo):
        """Test get_first_names quand généalogie non trouvée."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_first_names("NotFound")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_last_names_success(self, app_service, mock_repo):
        """Test get_last_names avec succès."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy
        mock_repo.get_last_names.return_value = ["Smith", "Johnson"]

        result = await app_service.get_last_names("Test")

        assert result == ["Smith", "Johnson"]

    @pytest.mark.asyncio
    async def test_get_last_names_not_found(self, app_service, mock_repo):
        """Test get_last_names quand généalogie non trouvée."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_last_names("NotFound")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_places_success(self, app_service, mock_repo):
        """Test get_places avec succès."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy
        mock_repo.get_places.return_value = ["Paris", "Lyon", "Marseille"]

        result = await app_service.get_places("Test")

        assert result == ["Paris", "Lyon", "Marseille"]
        mock_repo.get_places.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_places_not_found(self, app_service, mock_repo):
        """Test get_places quand généalogie non trouvée."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_places("NotFound")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_occupations_success(self, app_service, mock_repo):
        """Test get_occupations avec succès."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy
        mock_repo.get_occupations.return_value = ["Engineer", "Doctor"]

        result = await app_service.get_occupations("Test")

        assert result == ["Engineer", "Doctor"]

    @pytest.mark.asyncio
    async def test_get_occupations_not_found(self, app_service, mock_repo):
        """Test get_occupations quand généalogie non trouvée."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_occupations("NotFound")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_sources_success(self, app_service, mock_repo):
        """Test get_sources avec succès."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy
        mock_repo.get_sources.return_value = ["Census 1900", "Birth Certificate"]

        result = await app_service.get_sources("Test")

        assert result == ["Census 1900", "Birth Certificate"]

    @pytest.mark.asyncio
    async def test_get_sources_not_found(self, app_service, mock_repo):
        """Test get_sources quand généalogie non trouvée."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_sources("NotFound")

        assert result is None


class TestApplicationServiceStatistics:
    """Tests des méthodes de statistiques."""

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_last_births_success(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test get_last_births avec succès."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_person1 = Mock(
            id=1,
            first_name="Alice",
            surname="Smith",
            birth_date="15 JUN 2020",
        )
        mock_person2 = Mock(
            id=2,
            first_name="Bob",
            surname="Jones",
            birth_date="10 JAN 2019",
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [mock_person1, mock_person2]
        mock_db.query.return_value = mock_query

        result = await app_service.get_last_births("Test", limit=20)

        assert result is not None
        assert len(result) == 2
        assert result[0]["first_name"] == "Alice"
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_last_births_not_found(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test get_last_births quand généalogie non trouvée."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_last_births("NotFound")

        assert result is None

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_last_deaths_success(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test get_last_deaths avec succès."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_person = Mock(
            id=1,
            first_name="John",
            surname="Doe",
            death_date="20 DEC 2020",
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [mock_person]
        mock_db.query.return_value = mock_query

        result = await app_service.get_last_deaths("Test", limit=10)

        assert result is not None
        assert len(result) == 1
        assert result[0]["first_name"] == "John"
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_last_deaths_not_found(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test get_last_deaths quand généalogie non trouvée."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_last_deaths("NotFound")

        assert result is None

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_last_marriages_success(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test get_last_marriages avec succès."""
        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_repo.get_by_name.return_value = mock_genealogy

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_father = Mock(first_name="John", surname="Doe")
        mock_mother = Mock(first_name="Jane", surname="Smith")
        mock_family = Mock(
            id=1,
            marriage_date="15 JUN 2000",
            father=mock_father,
            mother=mock_mother,
        )

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [mock_family]
        mock_db.query.return_value = mock_query

        result = await app_service.get_last_marriages("Test", limit=10)

        assert result is not None
        assert len(result) == 1
        assert result[0]["father_first_name"] == "John"
        assert result[0]["mother_first_name"] == "Jane"
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.geneweb.application.services.SessionLocal")
    async def test_get_last_marriages_not_found(
        self, mock_session_local, app_service, mock_repo
    ):
        """Test get_last_marriages quand généalogie non trouvée."""
        mock_repo.get_by_name.return_value = None

        result = await app_service.get_last_marriages("NotFound")

        assert result is None


class TestGenealogyServiceExtended:
    """Tests étendus pour GenealogyService."""

    @patch("src.geneweb.application.services.SessionLocal")
    def test_import_gedcom_genealogy_not_found(self, mock_session_local):
        """Test import_gedcom quand la généalogie n'existe pas."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query

        service = GenealogyService()
        gedcom_content = "0 HEAD\n1 CHAR UTF-8\n0 TRLR"

        with pytest.raises(ValueError, match="not found"):
            service.import_gedcom("nonexistent", gedcom_content, mock_db)

    @patch("src.geneweb.application.services.SessionLocal")
    def test_export_gedcom_genealogy_not_found(self, mock_session_local):
        """Test export_gedcom quand la généalogie n'existe pas."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query

        service = GenealogyService()

        with pytest.raises(ValueError, match="not found"):
            service.export_gedcom(999, mock_db)

    @patch("src.geneweb.application.services.SessionLocal")
    def test_export_gedcom_success(self, mock_session_local):
        """Test export_gedcom avec succès basique."""
        mock_db = MagicMock()

        mock_genealogy = Mock(spec=Genealogy)
        mock_genealogy.id = 1
        mock_genealogy.name = "TestFamily"

        mock_person = Mock(spec=Person)
        mock_person.id = 1
        mock_person.first_name = "John"
        mock_person.surname = "Doe"
        mock_person.sex = Mock(value="M")  # Enum avec value
        mock_person.birth_date = "1980-01-15"
        mock_person.birth_place = "Paris"
        mock_person.death_date = None
        mock_person.death_place = None
        mock_person.baptism_date = None
        mock_person.baptism_place = None
        mock_person.burial_date = None
        mock_person.burial_place = None
        mock_person.occupation = "Engineer"
        mock_person.notes = "Test note"
        mock_person.child_of_families = []
        # Ajout des attributs de famille
        mock_person.families_as_father = []
        mock_person.families_as_mother = []

        mock_family = Mock(spec=Family)
        mock_family.id = 1
        mock_family.father_id = None
        mock_family.mother_id = None
        mock_family.marriage_date = None
        mock_family.marriage_place = None
        mock_family.children = []

        mock_query = Mock()
        mock_filter = Mock()

        def query_side_effect(model):
            q = Mock()
            f = Mock()
            q.filter.return_value = f
            if model == Genealogy:
                f.first.return_value = mock_genealogy
            elif model == Person:
                f.all.return_value = [mock_person]
            elif model == Family:
                f.all.return_value = [mock_family]
            return q

        mock_db.query.side_effect = query_side_effect

        service = GenealogyService()
        result = service.export_gedcom(1, mock_db)

        assert result is not None
        assert "0 HEAD" in result
        assert "INDI" in result or "FAM" in result  # Au moins un type d'enregistrement
        assert "0 TRLR" in result


class TestParseDateForSortingAdvanced:
    """Tests avancés pour parse_date_for_sorting."""

    def test_parse_date_with_before_prefix(self):
        """Test avec préfixe BEFORE/AVANT."""
        result = parse_date_for_sorting("BEFORE 1950")
        assert result[0] == 1950

    def test_parse_date_with_after_prefix(self):
        """Test avec préfixe AFTER/APRÈS."""
        result = parse_date_for_sorting("AFTER 1960")
        assert result[0] == 1960

    def test_parse_date_with_about_prefix_french(self):
        """Test avec préfixe français VERS."""
        result = parse_date_for_sorting("VERS 1975")
        assert result[0] == 1975

    def test_parse_date_with_estimated_prefix_french(self):
        """Test avec préfixe français ESTIME."""
        result = parse_date_for_sorting("ESTIME 1985")
        assert result[0] == 1985

    def test_parse_date_between_years(self):
        """Test avec format BETWEEN."""
        result = parse_date_for_sorting("BETWEEN 1980 AND 1990")
        assert result[0] == 1980

    def test_parse_date_complex_format(self):
        """Test avec format complexe."""
        result = parse_date_for_sorting("ABT 15 JUN 1980")
        assert result[0] == 1980

    def test_parse_date_only_year(self):
        """Test avec seulement une année."""
        result = parse_date_for_sorting("1999")
        assert result == (1999, 1, 1)

    def test_parse_date_invalid_format(self):
        """Test avec format invalide retourne valeur par défaut."""
        result = parse_date_for_sorting("Not a date")
        assert result == (9999, 12, 31)

    def test_parse_date_empty_string(self):
        """Test avec chaîne vide."""
        result = parse_date_for_sorting("")
        assert result == (9999, 12, 31)

    def test_parse_date_none_value(self):
        """Test avec None."""
        result = parse_date_for_sorting(None)
        assert result == (9999, 12, 31)


class TestIsPossiblyAliveAdvanced:
    """Tests avancés pour is_possibly_alive."""

    def test_person_with_death_date(self):
        """Test personne décédée."""
        assert is_possibly_alive("1900-01-01", "1980-12-31") is False

    def test_person_no_birth_date(self):
        """Test personne sans date de naissance."""
        assert is_possibly_alive(None, None) is False

    def test_person_invalid_birth_date(self):
        """Test personne avec date de naissance invalide."""
        assert is_possibly_alive("Invalid", None) is False

    def test_person_very_old(self):
        """Test personne très âgée (plus de 120 ans)."""
        assert is_possibly_alive("1850-01-01", None) is False

    def test_person_120_years_old(self):
        """Test personne exactement 120 ans."""
        current_year = datetime.now().year
        birth_year = current_year - 120
        assert is_possibly_alive(f"{birth_year}-01-01", None) is True

    def test_person_121_years_old(self):
        """Test personne 121 ans."""
        current_year = datetime.now().year
        birth_year = current_year - 121
        assert is_possibly_alive(f"{birth_year}-01-01", None) is False

    def test_person_young(self):
        """Test personne jeune."""
        current_year = datetime.now().year
        birth_year = current_year - 30
        assert is_possibly_alive(f"{birth_year}-01-01", None) is True

    def test_person_recent_birth(self):
        """Test personne née récemment."""
        current_year = datetime.now().year
        birth_year = current_year - 5
        assert is_possibly_alive(f"{birth_year}-01-01", None) is True

    def test_person_death_date_empty_string(self):
        """Test avec death_date chaîne vide."""
        # Une chaîne vide est considérée comme False, donc la personne peut être vivante
        assert is_possibly_alive("1980-01-01", "") is True

    def test_person_birth_date_with_prefix(self):
        """Test avec préfixe dans la date de naissance."""
        current_year = datetime.now().year
        birth_year = current_year - 50
        assert is_possibly_alive(f"ABT {birth_year}", None) is True
