"""Tests supplémentaires pour genealogy.py router"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from fastapi.responses import RedirectResponse

from src.geneweb.presentation.web.routers.genealogy import (
    manage_genealogy_page,
    rename_genealogy,
    delete_genealogy,
    advanced_genealogy_options_page,
    import_geneweb_page,
)


@pytest.fixture
def mock_request():
    """Mock FastAPI Request"""
    request = Mock(spec=Request)
    request.url_for = Mock(return_value="/test")
    return request


@pytest.fixture
def mock_app_service():
    """Mock ApplicationService"""
    service = Mock()
    return service


class TestManageGenealogyPage:
    """Tests pour manage_genealogy_page"""

    @pytest.mark.asyncio
    async def test_manage_genealogy_page(self, mock_request):
        """Test affichage page de gestion"""
        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates.TemplateResponse"
        ) as mock_template:
            mock_template.return_value = Mock()

            result = await manage_genealogy_page("test_gen", mock_request)

            assert mock_template.called


class TestRenameGenealogy:
    """Tests pour rename_genealogy"""

    @pytest.mark.asyncio
    async def test_rename_genealogy_success(self, mock_request, mock_app_service):
        """Test renommage réussi"""
        mock_app_service.rename_genealogy = AsyncMock(
            return_value=Mock(name="new_name", person_count=10)
        )
        mock_request.url_for = Mock(return_value="/genealogy/new_name")

        result = await rename_genealogy(
            "old_name", mock_request, "new_name", mock_app_service
        )

        assert isinstance(result, RedirectResponse)
        mock_app_service.rename_genealogy.assert_called_once_with(
            "old_name", "new_name"
        )

    @pytest.mark.asyncio
    async def test_rename_genealogy_not_found(self, mock_request, mock_app_service):
        """Test renommage généalogie inexistante"""
        mock_app_service.rename_genealogy = AsyncMock(return_value=None)

        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates.TemplateResponse"
        ) as mock_template:
            mock_template.return_value = Mock()

            result = await rename_genealogy(
                "old_name", mock_request, "new_name", mock_app_service
            )

            # Should return template with error
            assert mock_template.called


class TestDeleteGenealogy:
    """Tests pour delete_genealogy"""

    @pytest.mark.asyncio
    async def test_delete_genealogy_success(self, mock_request, mock_app_service):
        """Test suppression réussie"""
        mock_app_service.delete_genealogy = AsyncMock(return_value=True)
        mock_request.url_for = Mock(return_value="/genealogies")

        result = await delete_genealogy("test_gen", mock_request, mock_app_service)

        assert isinstance(result, RedirectResponse)
        mock_app_service.delete_genealogy.assert_called_once_with("test_gen")

    @pytest.mark.asyncio
    async def test_delete_genealogy_not_found(self, mock_request, mock_app_service):
        """Test suppression généalogie inexistante"""
        mock_app_service.delete_genealogy = AsyncMock(return_value=False)

        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates.TemplateResponse"
        ) as mock_template:
            mock_template.return_value = Mock()

            result = await delete_genealogy("test_gen", mock_request, mock_app_service)

            # Should return template with error
            assert mock_template.called


class TestAdvancedGenealogyOptionsPage:
    """Tests pour advanced_genealogy_options_page"""

    @pytest.mark.asyncio
    async def test_advanced_genealogy_options_page(self, mock_request):
        """Test affichage page options avancées"""
        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates.TemplateResponse"
        ) as mock_template:
            mock_template.return_value = Mock()

            result = await advanced_genealogy_options_page("test_gen", mock_request)

            assert mock_template.called


class TestImportGenewebPage:
    """Tests pour import_geneweb_page"""

    @pytest.mark.asyncio
    async def test_import_geneweb_page(self, mock_request):
        """Test affichage page import GeneWeb"""
        with patch(
            "src.geneweb.presentation.web.routers.genealogy.templates.TemplateResponse"
        ) as mock_template:
            mock_template.return_value = Mock()

            result = await import_geneweb_page(mock_request)

            assert mock_template.called
