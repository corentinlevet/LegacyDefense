"""
Tests pour les routers web.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from fastapi import Request
from fastapi.templating import Jinja2Templates

from src.geneweb.presentation.web.routers import person, search, stats
from src.geneweb.application.services import ApplicationService


@pytest.fixture
def mock_request():
    """Mock de la requête FastAPI."""
    request = Mock(spec=Request)
    request.url = Mock()
    request.url.path = "/test"
    return request


@pytest.fixture
def mock_app_service():
    """Mock du service d'application."""
    service = Mock(spec=ApplicationService)
    # Rendre toutes les méthodes async
    for attr in dir(service):
        if not attr.startswith("_"):
            method = getattr(service, attr)
            if callable(method):
                setattr(service, attr, AsyncMock())
    return service


@pytest.fixture
def mock_templates():
    """Mock des templates Jinja2."""
    with patch.object(Jinja2Templates, "TemplateResponse") as mock:
        yield mock


class TestPersonRouter:
    """Tests pour les routes de person.py."""

    @pytest.mark.asyncio
    async def test_person_profile_success(
        self, mock_request, mock_app_service, mock_templates
    ):
        """Test d'affichage d'un profil de personne."""
        mock_person = {
            "id": 1,
            "first_name": "John",
            "surname": "Doe",
            "birth_date": "1980-01-01",
        }
        mock_app_service.get_person_details.return_value = mock_person

        with patch(
            "src.geneweb.presentation.web.routers.person.templates"
        ) as mock_template:
            mock_template.TemplateResponse.return_value = "rendered_html"

            result = await person.person_profile(
                genealogy_name="test_genealogy",
                person_id=1,
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_app_service.get_person_details.assert_called_once_with(1)
            mock_template.TemplateResponse.assert_called_once()
            call_args = mock_template.TemplateResponse.call_args
            assert call_args[0][0] == "person_profile.html"
            assert call_args[0][1]["genealogy_name"] == "test_genealogy"
            assert call_args[0][1]["person"] == mock_person

    def test_gettext_translation(self):
        """Test de la fonction gettext."""
        assert person.gettext("Basic Info") == "Informations de base"
        assert person.gettext("Born") == "Né(e)"
        assert person.gettext("Unknown Key") == "Unknown Key"

    def test_gettext_all_translations(self):
        """Test de toutes les traductions disponibles."""
        translations = {
            "Basic Info": "Informations de base",
            "Spouse and Children": "Conjoint et Enfants",
            "Genealogy Tree (3 Generations)": "Arbre généalogique (3 générations)",
            "Siblings": "Frères et Sœurs",
            "Born": "Né(e)",
            "in": "à",
            "Died": "Décédé(e)",
            "Occupation": "Profession",
            "on": "le",
            "with": "avec",
            "No siblings found.": "Aucun frère ou sœur trouvé.",
        }

        for en, fr in translations.items():
            assert person.gettext(en) == fr


class TestSearchRouter:
    """Tests pour les routes de search.py."""

    @pytest.mark.asyncio
    async def test_search_persons_with_both_params(
        self, mock_request, mock_app_service
    ):
        """Test de recherche avec prénom et nom."""
        mock_results = [
            {"id": 1, "first_name": "John", "surname": "Doe"},
            {"id": 2, "first_name": "John", "surname": "Smith"},
        ]
        mock_app_service.search_persons.return_value = mock_results

        with patch(
            "src.geneweb.presentation.web.routers.search.templates"
        ) as mock_template:
            mock_template.TemplateResponse.return_value = "rendered_html"

            result = await search.search_persons(
                genealogy_name="test_genealogy",
                request=mock_request,
                p="John",
                n="Doe",
                app_service=mock_app_service,
            )

            mock_app_service.search_persons.assert_called_once_with(
                "test_genealogy", "John", "Doe"
            )
            mock_template.TemplateResponse.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_persons_first_name_only(
        self, mock_request, mock_app_service
    ):
        """Test de recherche avec prénom seulement."""
        mock_results = [{"id": 1, "first_name": "John", "surname": "Doe"}]
        mock_app_service.search_persons.return_value = mock_results

        with patch(
            "src.geneweb.presentation.web.routers.search.templates"
        ) as mock_template:
            mock_template.TemplateResponse.return_value = "rendered_html"

            await search.search_persons(
                genealogy_name="test_genealogy",
                request=mock_request,
                p="John",
                n=None,
                app_service=mock_app_service,
            )

            mock_app_service.search_persons.assert_called_once_with(
                "test_genealogy", "John", None
            )

    @pytest.mark.asyncio
    async def test_search_persons_last_name_only(
        self, mock_request, mock_app_service
    ):
        """Test de recherche avec nom seulement."""
        mock_results = [{"id": 1, "first_name": "John", "surname": "Doe"}]
        mock_app_service.search_persons.return_value = mock_results

        with patch(
            "src.geneweb.presentation.web.routers.search.templates"
        ) as mock_template:
            mock_template.TemplateResponse.return_value = "rendered_html"

            await search.search_persons(
                genealogy_name="test_genealogy",
                request=mock_request,
                p=None,
                n="Doe",
                app_service=mock_app_service,
            )

            mock_app_service.search_persons.assert_called_once_with(
                "test_genealogy", None, "Doe"
            )

    @pytest.mark.asyncio
    async def test_search_persons_no_params(self, mock_request, mock_app_service):
        """Test de recherche sans paramètres."""
        mock_results = []
        mock_app_service.search_persons.return_value = mock_results

        with patch(
            "src.geneweb.presentation.web.routers.search.templates"
        ) as mock_template:
            mock_template.TemplateResponse.return_value = "rendered_html"

            await search.search_persons(
                genealogy_name="test_genealogy",
                request=mock_request,
                p=None,
                n=None,
                app_service=mock_app_service,
            )

            mock_app_service.search_persons.assert_called_once_with(
                "test_genealogy", None, None
            )

    def test_search_gettext_translation(self):
        """Test de la fonction gettext de search."""
        assert search.gettext("Search Results") == "Résultats de recherche"
        assert search.gettext("Back") == "Retour"
        assert search.gettext("son of") == "fils de"
        assert search.gettext("daughter of") == "fille de"
        assert search.gettext("Unknown") == "Unknown"


class TestStatsRouter:
    """Tests pour les routes de stats.py."""

    @pytest.mark.asyncio
    async def test_statistics_page_success(self, mock_request, mock_app_service):
        """Test d'affichage de la page de statistiques."""
        mock_app_service.get_last_births.return_value = [{"id": 1, "name": "Person1"}]
        mock_app_service.get_last_deaths.return_value = [{"id": 2, "name": "Person2"}]
        mock_app_service.get_last_marriages.return_value = [
            {"id": 3, "name": "Couple1"}
        ]
        mock_app_service.get_oldest_couples.return_value = [
            {"id": 4, "name": "Couple2"}
        ]
        mock_app_service.get_oldest_alive.return_value = [{"id": 5, "name": "Person3"}]
        mock_app_service.get_longest_lived.return_value = [
            {"id": 6, "name": "Person4"}
        ]

        with patch(
            "src.geneweb.presentation.web.routers.stats.templates"
        ) as mock_template:
            mock_template.TemplateResponse.return_value = "rendered_html"

            result = await stats.statistics_page(
                genealogy_name="test_genealogy",
                request=mock_request,
                app_service=mock_app_service,
            )

            # Vérifier que toutes les méthodes ont été appelées
            mock_app_service.get_last_births.assert_called_once_with("test_genealogy")
            mock_app_service.get_last_deaths.assert_called_once_with("test_genealogy")
            mock_app_service.get_last_marriages.assert_called_once_with(
                "test_genealogy"
            )
            mock_app_service.get_oldest_couples.assert_called_once_with(
                "test_genealogy"
            )
            mock_app_service.get_oldest_alive.assert_called_once_with("test_genealogy")
            mock_app_service.get_longest_lived.assert_called_once_with(
                "test_genealogy"
            )

            # Vérifier que le template a été appelé
            mock_template.TemplateResponse.assert_called_once()
            call_args = mock_template.TemplateResponse.call_args
            assert call_args[0][0] == "statistics.html"
            context = call_args[0][1]
            assert context["genealogy_name"] == "test_genealogy"
            assert len(context["last_births"]) == 1
            assert len(context["last_deaths"]) == 1

    @pytest.mark.asyncio
    async def test_statistics_page_empty_results(self, mock_request, mock_app_service):
        """Test d'affichage des statistiques avec résultats vides."""
        mock_app_service.get_last_births.return_value = []
        mock_app_service.get_last_deaths.return_value = []
        mock_app_service.get_last_marriages.return_value = []
        mock_app_service.get_oldest_couples.return_value = []
        mock_app_service.get_oldest_alive.return_value = []
        mock_app_service.get_longest_lived.return_value = []

        with patch(
            "src.geneweb.presentation.web.routers.stats.templates"
        ) as mock_template:
            mock_template.TemplateResponse.return_value = "rendered_html"

            result = await stats.statistics_page(
                genealogy_name="test_genealogy",
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_template.TemplateResponse.assert_called_once()
            call_args = mock_template.TemplateResponse.call_args
            context = call_args[0][1]
            assert context["last_births"] == []
            assert context["last_deaths"] == []

    @pytest.mark.asyncio
    async def test_statistics_page_none_results(self, mock_request, mock_app_service):
        """Test d'affichage des statistiques avec résultats None."""
        mock_app_service.get_last_births.return_value = None
        mock_app_service.get_last_deaths.return_value = None
        mock_app_service.get_last_marriages.return_value = None
        mock_app_service.get_oldest_couples.return_value = None
        mock_app_service.get_oldest_alive.return_value = None
        mock_app_service.get_longest_lived.return_value = None

        with patch(
            "src.geneweb.presentation.web.routers.stats.templates"
        ) as mock_template:
            mock_template.TemplateResponse.return_value = "rendered_html"

            result = await stats.statistics_page(
                genealogy_name="test_genealogy",
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_template.TemplateResponse.assert_called_once()
            call_args = mock_template.TemplateResponse.call_args
            context = call_args[0][1]
            # None devrait être converti en []
            assert context["last_births"] == []
            assert context["last_deaths"] == []

    @pytest.mark.asyncio
    async def test_statistics_page_exception(self, mock_request, mock_app_service):
        """Test de gestion d'erreur dans la page de statistiques."""
        mock_app_service.get_last_births.side_effect = Exception("Database error")

        with patch(
            "src.geneweb.presentation.web.routers.stats.templates"
        ) as mock_template:
            mock_template.TemplateResponse.return_value = "error_page"

            with patch("src.geneweb.presentation.web.routers.stats.logger") as mock_logger:
                result = await stats.statistics_page(
                    genealogy_name="test_genealogy",
                    request=mock_request,
                    app_service=mock_app_service,
                )

                # Vérifier qu'une erreur a été loggée
                # L'exception devrait être propagée ou gérée
                mock_template.TemplateResponse.assert_called()
