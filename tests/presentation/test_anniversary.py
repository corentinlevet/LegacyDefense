"""Tests pour les routers anniversary.py"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request
from fastapi.templating import Jinja2Templates

from src.geneweb.presentation.web.routers.anniversary import (
    anniversaries_menu,
    birth_anniversaries,
    death_anniversaries,
    marriage_anniversaries,
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


class TestAnniversariesMenu:
    """Tests pour anniversaries_menu"""

    @pytest.mark.asyncio
    async def test_anniversaries_menu(self, mock_request):
        """Test affichage du menu des anniversaires"""
        with patch(
            "src.geneweb.presentation.web.routers.anniversary.templates.TemplateResponse"
        ) as mock_template:
            mock_template.return_value = Mock()

            result = await anniversaries_menu("test_gen", mock_request)

            assert mock_template.called


class TestBirthAnniversaries:
    """Tests pour birth_anniversaries"""

    @pytest.mark.asyncio
    async def test_birth_anniversaries_no_month(self, mock_request, mock_app_service):
        """Test anniversaires de naissance sans mois spécifique"""
        mock_app_service.get_birth_anniversaries = AsyncMock(
            side_effect=[
                [{"id": 1, "first_name": "John", "surname": "Doe", "age": 50}],  # today
                [],  # tomorrow
                [],  # day after
            ]
        )

        with patch(
            "src.geneweb.presentation.web.routers.anniversary.templates.TemplateResponse"
        ) as mock_template:
            mock_template.return_value = Mock()

            result = await birth_anniversaries(
                "test_gen", mock_request, app_service=mock_app_service
            )

            assert mock_template.called
            assert mock_app_service.get_birth_anniversaries.call_count == 3


class TestDeathAnniversaries:
    """Tests pour death_anniversaries"""

    @pytest.mark.asyncio
    async def test_death_anniversaries_no_month(self, mock_request, mock_app_service):
        """Test anniversaires de décès sans mois spécifique"""
        mock_app_service.get_death_anniversaries = AsyncMock(
            side_effect=[
                [
                    {
                        "id": 1,
                        "first_name": "John",
                        "surname": "Doe",
                        "years_since_death": 10,
                    }
                ],  # today
                [],  # tomorrow
                [],  # day after
            ]
        )

        with patch(
            "src.geneweb.presentation.web.routers.anniversary.templates.TemplateResponse"
        ) as mock_template:
            mock_template.return_value = Mock()

            result = await death_anniversaries(
                "test_gen", mock_request, app_service=mock_app_service
            )

            assert mock_template.called
            assert mock_app_service.get_death_anniversaries.call_count == 3


class TestMarriageAnniversaries:
    """Tests pour marriage_anniversaries"""

    @pytest.mark.asyncio
    async def test_marriage_anniversaries_no_month(
        self, mock_request, mock_app_service
    ):
        """Test anniversaires de mariage sans mois spécifique"""
        mock_app_service.get_marriage_anniversaries = AsyncMock(
            side_effect=[
                [
                    {
                        "id": 1,
                        "father_first_name": "John",
                        "father_surname": "Doe",
                        "mother_first_name": "Jane",
                        "mother_surname": "Smith",
                        "years_of_marriage": 25,
                    }
                ],  # today
                [],  # tomorrow
                [],  # day after
            ]
        )

        with patch(
            "src.geneweb.presentation.web.routers.anniversary.templates.TemplateResponse"
        ) as mock_template:
            mock_template.return_value = Mock()

            result = await marriage_anniversaries(
                "test_gen", mock_request, app_service=mock_app_service
            )

            assert mock_template.called
            assert mock_app_service.get_marriage_anniversaries.call_count == 3
