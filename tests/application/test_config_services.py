"""
Tests pour les services de configuration.
"""

from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy.orm import Session

from src.geneweb.application.config_services import (
    get_genealogy_config,
    get_server_config,
    update_genealogy_config,
    update_server_config,
)
from src.geneweb.infrastructure.config_models import GenealogyConfig, ServerConfig
from src.geneweb.infrastructure.models import Genealogy


@pytest.fixture
def mock_db():
    """Mock de la session de base de données."""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_genealogy():
    """Généalogie de test."""
    genealogy = Genealogy()
    genealogy.id = 1
    genealogy.name = "test_genealogy"
    return genealogy


@pytest.fixture
def sample_genealogy_config():
    """Configuration de généalogie de test."""
    config = GenealogyConfig()
    config.id = 1
    config.genealogy_id = 1
    config.default_lang = "fr"
    config.max_anc_level = 12
    config.max_desc_level = 12
    config.history = True
    return config


@pytest.fixture
def sample_server_config():
    """Configuration serveur de test."""
    config = ServerConfig()
    config.id = 1
    config.default_lang = "fr"
    config.only = ""
    config.log = ""
    return config


class TestGetGenealogyConfig:
    """Tests pour get_genealogy_config."""

    def test_get_genealogy_config_success(
        self, mock_db, sample_genealogy, sample_genealogy_config
    ):
        """Test de récupération réussie d'une configuration."""
        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.side_effect = [sample_genealogy, sample_genealogy_config]
        mock_db.query.return_value = mock_query

        result = get_genealogy_config("test_genealogy", mock_db)

        assert result == sample_genealogy_config
        assert result.genealogy_id == 1
        assert result.default_lang == "fr"

    def test_get_genealogy_config_genealogy_not_found(self, mock_db):
        """Test quand la généalogie n'existe pas."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query

        result = get_genealogy_config("nonexistent", mock_db)

        assert result is None

    def test_get_genealogy_config_no_config(self, mock_db, sample_genealogy):
        """Test quand la généalogie existe mais n'a pas de config."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.side_effect = [sample_genealogy, None]
        mock_db.query.return_value = mock_query

        result = get_genealogy_config("test_genealogy", mock_db)

        assert result is None


class TestUpdateGenealogyConfig:
    """Tests pour update_genealogy_config."""

    def test_update_existing_config(
        self, mock_db, sample_genealogy, sample_genealogy_config
    ):
        """Test de mise à jour d'une configuration existante."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.side_effect = [sample_genealogy, sample_genealogy_config]
        mock_db.query.return_value = mock_query

        config_data = {"default_lang": "en", "max_anc_level": 15}
        result = update_genealogy_config("test_genealogy", config_data, mock_db)

        assert result is not None
        assert result.default_lang == "en"
        assert result.max_anc_level == 15
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_new_config(self, mock_db, sample_genealogy):
        """Test de création d'une nouvelle configuration."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.side_effect = [sample_genealogy, None]
        mock_db.query.return_value = mock_query

        config_data = {"default_lang": "en", "max_anc_level": 15}
        result = update_genealogy_config("test_genealogy", config_data, mock_db)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_config_genealogy_not_found(self, mock_db):
        """Test quand la généalogie n'existe pas."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query

        config_data = {"default_lang": "en"}
        result = update_genealogy_config("nonexistent", config_data, mock_db)

        assert result is None
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_update_config_ignore_invalid_fields(
        self, mock_db, sample_genealogy, sample_genealogy_config
    ):
        """Test que les champs invalides sont ignorés."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.side_effect = [sample_genealogy, sample_genealogy_config]
        mock_db.query.return_value = mock_query

        config_data = {"invalid_field": "value", "default_lang": "de"}
        result = update_genealogy_config("test_genealogy", config_data, mock_db)

        assert result is not None
        assert result.default_lang == "de"
        assert not hasattr(result, "invalid_field")


class TestGetServerConfig:
    """Tests pour get_server_config."""

    def test_get_existing_server_config(self, mock_db, sample_server_config):
        """Test de récupération d'une configuration serveur existante."""
        mock_query = Mock()
        mock_query.first.return_value = sample_server_config
        mock_db.query.return_value = mock_query

        result = get_server_config(mock_db)

        assert result == sample_server_config
        assert result.default_lang == "fr"
        mock_db.add.assert_not_called()

    def test_create_default_server_config(self, mock_db):
        """Test de création d'une configuration serveur par défaut."""
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = get_server_config(mock_db)

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


class TestUpdateServerConfig:
    """Tests pour update_server_config."""

    def test_update_existing_server_config(self, mock_db, sample_server_config):
        """Test de mise à jour d'une configuration serveur existante."""
        mock_query = Mock()
        mock_query.first.return_value = sample_server_config
        mock_db.query.return_value = mock_query

        config_data = {"default_lang": "en", "log": "/var/log/geneweb.log"}
        result = update_server_config(config_data, mock_db)

        assert result is not None
        assert result.default_lang == "en"
        assert result.log == "/var/log/geneweb.log"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_new_server_config(self, mock_db):
        """Test de création d'une nouvelle configuration serveur."""
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        config_data = {"default_lang": "es"}
        result = update_server_config(config_data, mock_db)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_server_config_ignore_invalid_fields(
        self, mock_db, sample_server_config
    ):
        """Test que les champs invalides sont ignorés."""
        mock_query = Mock()
        mock_query.first.return_value = sample_server_config
        mock_db.query.return_value = mock_query

        config_data = {"invalid_field": "value", "default_lang": "it"}
        result = update_server_config(config_data, mock_db)

        assert result is not None
        assert result.default_lang == "it"
        assert not hasattr(result, "invalid_field")

    def test_update_server_config_empty_data(self, mock_db, sample_server_config):
        """Test avec des données vides."""
        mock_query = Mock()
        mock_query.first.return_value = sample_server_config
        mock_db.query.return_value = mock_query

        config_data = {}
        result = update_server_config(config_data, mock_db)

        assert result is not None
        mock_db.commit.assert_called_once()
