"""
Tests pour les dépendances FastAPI.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock

from src.geneweb.presentation.dependencies import get_db, get_app_service
from src.geneweb.application.services import ApplicationService
from src.geneweb.infrastructure.repositories.sql_genealogy_repository import (
    SQLGenealogyRepository,
)


class TestGetDb:
    """Tests pour get_db."""

    @patch("src.geneweb.presentation.dependencies.SessionLocal")
    def test_get_db_yields_session(self, mock_session_local):
        """Test que get_db retourne une session."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Utiliser le générateur
        gen = get_db()
        db = next(gen)

        assert db == mock_db
        mock_session_local.assert_called_once()

    @patch("src.geneweb.presentation.dependencies.SessionLocal")
    def test_get_db_closes_session(self, mock_session_local):
        """Test que get_db ferme la session après utilisation."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Utiliser le générateur complètement
        gen = get_db()
        db = next(gen)
        try:
            next(gen)
        except StopIteration:
            pass

        mock_db.close.assert_called_once()

    @patch("src.geneweb.presentation.dependencies.SessionLocal")
    def test_get_db_closes_on_exception(self, mock_session_local):
        """Test que get_db ferme la session même en cas d'exception."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        gen = get_db()
        db = next(gen)

        # Simuler une exception dans le code utilisant la session
        try:
            gen.throw(Exception("Test exception"))
        except Exception:
            pass

        mock_db.close.assert_called_once()


class TestGetAppService:
    """Tests pour get_app_service."""

    def test_get_app_service_returns_service(self):
        """Test que get_app_service retourne un ApplicationService."""
        mock_db = MagicMock()

        result = get_app_service(mock_db)

        assert isinstance(result, ApplicationService)
        assert isinstance(result.genealogy_repo, SQLGenealogyRepository)

    def test_get_app_service_with_different_db(self):
        """Test avec différentes sessions DB."""
        mock_db1 = MagicMock()
        mock_db2 = MagicMock()

        result1 = get_app_service(mock_db1)
        result2 = get_app_service(mock_db2)

        # Les services doivent être différents
        assert result1 is not result2
        # Les repos doivent être différents
        assert result1.genealogy_repo is not result2.genealogy_repo

    @patch("src.geneweb.presentation.dependencies.SQLGenealogyRepository")
    @patch("src.geneweb.presentation.dependencies.ApplicationService")
    def test_get_app_service_initialization(
        self, mock_app_service, mock_repo_class
    ):
        """Test que get_app_service initialise correctement le service."""
        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_service = MagicMock()
        mock_app_service.return_value = mock_service

        result = get_app_service(mock_db)

        mock_repo_class.assert_called_once_with(mock_db)
        mock_app_service.assert_called_once_with(mock_repo)
        assert result == mock_service
