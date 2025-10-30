"""Tests pour server_api.py"""

import pytest
from unittest.mock import Mock, patch

from src.geneweb.presentation.api.server_api import (
    get_server_config_api,
    update_server_config_api,
    ServerConfigRequest,
)


class TestGetServerConfigAPI:
    """Tests pour get_server_config_api"""

    def test_get_server_config_success(self):
        """Test récupération config serveur réussie"""
        mock_config = Mock(
            default_lang="fr",
            only="",
            log="",
        )
        mock_db = Mock()

        with patch(
            "src.geneweb.presentation.api.server_api.config_services.get_server_config",
            return_value=mock_config,
        ):
            result = get_server_config_api(mock_db)

            assert result["default_lang"] == "fr"
            assert result["only"] == ""
            assert result["log"] == ""

class TestUpdateServerConfigAPI:
    """Tests pour update_server_config_api"""

    def test_update_server_config_success(self):
        """Test mise à jour config serveur réussie"""
        request = ServerConfigRequest(
            default_lang="en", only="genealogy1", log="/var/log/geneweb.log"
        )
        mock_db = Mock()

        with patch(
            "src.geneweb.presentation.api.server_api.config_services.update_server_config",
            return_value=Mock(),
        ):
            result = update_server_config_api(request, mock_db)

            assert result["message"] == "Server configuration updated successfully"

    def test_update_server_config_partial(self):
        """Test mise à jour partielle config serveur"""
        request = ServerConfigRequest(default_lang="en")
        mock_db = Mock()

        with patch(
            "src.geneweb.presentation.api.server_api.config_services.update_server_config",
            return_value=Mock(),
        ):
            result = update_server_config_api(request, mock_db)

            assert result["message"] == "Server configuration updated successfully"
