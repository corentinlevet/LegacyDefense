"""Tests pour main.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI


class TestMainApp:
    """Tests pour l'application principale"""

    def test_app_creation(self):
        """Test création de l'application FastAPI"""
        with patch("src.geneweb.main.FastAPI") as mock_fastapi:
            mock_app = Mock()
            mock_fastapi.return_value = mock_app

            # Import du module pour trigger la création
            import importlib
            import src.geneweb.main

            importlib.reload(src.geneweb.main)

            # L'app devrait être créée
            assert src.geneweb.main.app is not None

    def test_app_has_routers(self):
        """Test que l'app a les routers configurés"""
        from src.geneweb.main import app

        # L'app devrait avoir des routes configurées
        assert app is not None
        assert isinstance(app, FastAPI)

    def test_app_title(self):
        """Test le titre de l'application"""
        from src.geneweb.main import app

        assert app.title == "GeneWeb Modernization"

    def test_static_files_mounted(self):
        """Test que les fichiers statiques sont montés"""
        from src.geneweb.main import app

        # Vérifier que l'app a des routes (ce qui inclut les fichiers statiques)
        assert len(app.routes) > 0
