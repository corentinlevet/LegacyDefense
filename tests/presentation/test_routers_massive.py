"""
Tests massifs pour les routers web restants.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

from src.geneweb.application.services import ApplicationService
from src.geneweb.presentation.web.routers import base, book, family, genealogy, places


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
    for attr in dir(service):
        if not attr.startswith("_") and callable(getattr(service, attr, None)):
            setattr(service, attr, AsyncMock())
    return service


class TestBookRouter:
    """Tests pour book.py."""

    @pytest.mark.asyncio
    async def test_book_first_names_success(self, mock_request, mock_app_service):
        """Test affichage du livre des prénoms."""
        mock_app_service.get_first_names.return_value = ["Alice", "Bob", "Charlie"]

        with patch("src.geneweb.presentation.web.routers.book.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await book.book_first_names(
                genealogy_name="test",
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_app_service.get_first_names.assert_called_once_with("test")
            mock_tpl.TemplateResponse.assert_called_once()
            args = mock_tpl.TemplateResponse.call_args[0]
            assert args[0] == "book_first_names.html"
            assert args[1]["genealogy_name"] == "test"
            assert len(args[1]["first_names"]) == 3

    @pytest.mark.asyncio
    async def test_book_first_names_not_found(self, mock_request, mock_app_service):
        """Test quand la généalogie n'existe pas."""
        mock_app_service.get_first_names.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await book.book_first_names(
                genealogy_name="notfound",
                request=mock_request,
                app_service=mock_app_service,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_book_last_names_success(self, mock_request, mock_app_service):
        """Test affichage du livre des noms."""
        mock_app_service.get_last_names.return_value = ["Smith", "Johnson"]

        with patch("src.geneweb.presentation.web.routers.book.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await book.book_last_names(
                genealogy_name="test",
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_app_service.get_last_names.assert_called_once_with("test")
            mock_tpl.TemplateResponse.assert_called_once()

    @pytest.mark.asyncio
    async def test_book_last_names_not_found(self, mock_request, mock_app_service):
        """Test livre des noms quand généalogie non trouvée."""
        mock_app_service.get_last_names.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await book.book_last_names(
                genealogy_name="notfound",
                request=mock_request,
                app_service=mock_app_service,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_book_places_success(self, mock_request, mock_app_service):
        """Test affichage du livre des lieux."""
        mock_app_service.get_places.return_value = ["Paris", "Lyon"]

        with patch("src.geneweb.presentation.web.routers.book.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await book.book_places(
                genealogy_name="test",
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_app_service.get_places.assert_called_once_with("test")

    @pytest.mark.asyncio
    async def test_book_places_not_found(self, mock_request, mock_app_service):
        """Test livre des lieux quand généalogie non trouvée."""
        mock_app_service.get_places.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await book.book_places(
                genealogy_name="notfound",
                request=mock_request,
                app_service=mock_app_service,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_book_occupations_success(self, mock_request, mock_app_service):
        """Test affichage du livre des professions."""
        mock_app_service.get_occupations.return_value = ["Engineer", "Doctor"]

        with patch("src.geneweb.presentation.web.routers.book.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await book.book_occupations(
                genealogy_name="test",
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_app_service.get_occupations.assert_called_once_with("test")

    @pytest.mark.asyncio
    async def test_book_occupations_not_found(self, mock_request, mock_app_service):
        """Test livre des professions quand généalogie non trouvée."""
        mock_app_service.get_occupations.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await book.book_occupations(
                genealogy_name="notfound",
                request=mock_request,
                app_service=mock_app_service,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_book_sources_success(self, mock_request, mock_app_service):
        """Test affichage du livre des sources."""
        mock_app_service.get_sources.return_value = ["Census 1900"]

        with patch("src.geneweb.presentation.web.routers.book.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await book.book_sources(
                genealogy_name="test",
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_app_service.get_sources.assert_called_once_with("test")

    @pytest.mark.asyncio
    async def test_book_sources_not_found(self, mock_request, mock_app_service):
        """Test livre des sources quand généalogie non trouvée."""
        mock_app_service.get_sources.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await book.book_sources(
                genealogy_name="notfound",
                request=mock_request,
                app_service=mock_app_service,
            )

        assert exc_info.value.status_code == 404


class TestFamilyRouter:
    """Tests pour family.py."""

    @pytest.mark.asyncio
    async def test_add_family_form(self, mock_request):
        """Test affichage du formulaire d'ajout de famille."""
        with patch("src.geneweb.presentation.web.routers.family.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await family.add_family_form(
                genealogy_name="test", request=mock_request
            )

            mock_tpl.TemplateResponse.assert_called_once()
            args = mock_tpl.TemplateResponse.call_args[0]
            assert args[0] == "add_family.html"
            assert args[1]["genealogy_name"] == "test"

    @pytest.mark.asyncio
    async def test_add_family_post(self, mock_request, mock_app_service):
        """Test soumission du formulaire d'ajout de famille."""
        mock_request.form = AsyncMock(return_value={"father_name": "John"})
        mock_app_service.add_family.return_value = 123

        result = await family.add_family_post(
            genealogy_name="test",
            request=mock_request,
            app_service=mock_app_service,
        )

        assert result.status_code == 303
        assert "/genealogy/test/family/123" in result.headers["location"]

    @pytest.mark.asyncio
    async def test_family_created(self, mock_request, mock_app_service):
        """Test affichage de la confirmation de création de famille."""
        mock_family = {"id": 123, "father": "John", "mother": "Jane"}
        mock_app_service.get_family.return_value = mock_family

        with patch("src.geneweb.presentation.web.routers.family.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await family.family_created(
                genealogy_name="test",
                family_id=123,
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_app_service.get_family.assert_called_once_with(123)

    def test_family_gettext(self):
        """Test fonction gettext de family."""
        assert family.gettext("Family Created") == "Famille créée"
        assert family.gettext("Parents") == "Parents"
        assert family.gettext("Unknown") == "Unknown"


class TestGenealogyRouter:
    """Tests pour genealogy.py."""

    @pytest.mark.asyncio
    async def test_create_genealogy_form(self, mock_request):
        """Test affichage du formulaire de création de généalogie."""
        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates"
        ) as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await genealogy.create_genealogy_form(request=mock_request)

            mock_tpl.TemplateResponse.assert_called_once()
            args = mock_tpl.TemplateResponse.call_args[0]
            assert args[0] == "create_genealogy.html"

    @pytest.mark.asyncio
    async def test_list_genealogies_page(self, mock_request):
        """Test affichage de la liste des généalogies."""
        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates"
        ) as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await genealogy.list_genealogies_page(request=mock_request)

            mock_tpl.TemplateResponse.assert_called_once()
            args = mock_tpl.TemplateResponse.call_args[0]
            assert args[0] == "list_genealogies.html"

    @pytest.mark.asyncio
    async def test_view_genealogy_success(self, mock_request, mock_app_service):
        """Test affichage du dashboard d'une généalogie."""
        mock_details = Mock(person_count=150)
        mock_app_service.get_genealogy_details.return_value = mock_details

        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates"
        ) as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await genealogy.view_genealogy(
                name="test", request=mock_request, app_service=mock_app_service
            )

            mock_app_service.get_genealogy_details.assert_called_once_with("test")
            mock_tpl.TemplateResponse.assert_called_once()
            args = mock_tpl.TemplateResponse.call_args[0]
            assert args[1]["genealogy_name"] == "test"
            assert args[1]["nb_persons"] == 150

    @pytest.mark.asyncio
    async def test_view_genealogy_not_found(self, mock_request, mock_app_service):
        """Test affichage d'une généalogie non trouvée."""
        mock_app_service.get_genealogy_details.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await genealogy.view_genealogy(
                name="notfound", request=mock_request, app_service=mock_app_service
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_import_gedcom_page(self, mock_request):
        """Test affichage de la page d'import GEDCOM."""
        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates"
        ) as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await genealogy.import_gedcom_page(
                genealogy_name="test", request=mock_request
            )

            mock_tpl.TemplateResponse.assert_called_once()
            args = mock_tpl.TemplateResponse.call_args[0]
            assert args[0] == "import_gedcom.html"

    @pytest.mark.asyncio
    async def test_export_gedcom_page(self, mock_request):
        """Test affichage de la page d'export GEDCOM."""
        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates"
        ) as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await genealogy.export_gedcom_page(
                genealogy_name="test", request=mock_request
            )

            mock_tpl.TemplateResponse.assert_called_once()


class TestBaseRouter:
    """Tests pour base.py."""

    @pytest.mark.asyncio
    async def test_read_start_page(self, mock_request):
        """Test affichage de la page de démarrage."""
        with patch("src.geneweb.presentation.web.routers.base.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await base.read_start_page(request=mock_request)

            mock_tpl.TemplateResponse.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_select_page(self, mock_request):
        """Test affichage de la page de sélection."""
        with patch("src.geneweb.presentation.web.routers.base.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await base.read_select_page(request=mock_request)

            mock_tpl.TemplateResponse.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_admin_page(self, mock_request):
        """Test affichage de la page admin."""
        with patch("src.geneweb.presentation.web.routers.base.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await base.read_admin_page(request=mock_request)

            mock_tpl.TemplateResponse.assert_called_once()


class TestPlacesRouter:
    """Tests pour places.py."""

    @pytest.mark.asyncio
    async def test_places_surnames_success(self, mock_request, mock_app_service):
        """Test affichage des noms de famille par lieu."""
        mock_data = {"Paris": ["Smith", "Johnson"], "Lyon": ["Martin"]}
        mock_app_service.get_places_surnames.return_value = mock_data

        with patch("src.geneweb.presentation.web.routers.places.templates") as mock_tpl:
            mock_tpl.TemplateResponse.return_value = "rendered"

            result = await places.places_surnames(
                genealogy_name="test",
                request=mock_request,
                app_service=mock_app_service,
            )

            mock_app_service.get_places_surnames.assert_called_once_with("test")
            mock_tpl.TemplateResponse.assert_called_once()
