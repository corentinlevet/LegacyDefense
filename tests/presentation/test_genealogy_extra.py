"""Tests supplémentaires pour genealogy.py router"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request
from fastapi.responses import RedirectResponse

from src.geneweb.presentation.web.routers.genealogy import (
    advanced_genealogy_options_page,
    delete_genealogy,
    import_geneweb_page,
    manage_genealogy_page,
    rename_genealogy,
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
