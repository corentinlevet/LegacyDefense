"""
Tests pour les services de configuration.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.geneweb.infrastructure.database import Base
from src.geneweb.infrastructure.models import Genealogy
from src.geneweb.infrastructure.config_models import GenealogyConfig, ServerConfig
from src.geneweb.application.config_services import (
    get_genealogy_config,
    update_genealogy_config,
    get_server_config,
    update_server_config,
)


@pytest.fixture
def test_db():
    """Crée une base de données de test en mémoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_genealogy(test_db):
    """Crée une généalogie de test."""
    genealogy = Genealogy(name="TestFamily")
    test_db.add(genealogy)
    test_db.commit()
    test_db.refresh(genealogy)
    return genealogy


class TestGetGenealogyConfig:
    """Tests pour get_genealogy_config."""

    def test_get_config_existing(self, test_db, sample_genealogy):
        """Test récupération d'une config existante."""
        # Créer une config
        config = GenealogyConfig(
            genealogy_id=sample_genealogy.id,
            wizard="friend",
            friend="on"
        )
        test_db.add(config)
        test_db.commit()
        
        # Récupérer la config
        result = get_genealogy_config("TestFamily", test_db)
        
        assert result is not None
        assert result.genealogy_id == sample_genealogy.id
        assert result.wizard == "friend"
        assert result.friend == "on"

    def test_get_config_non_existing(self, test_db, sample_genealogy):
        """Test récupération d'une config inexistante."""
        result = get_genealogy_config("TestFamily", test_db)
        assert result is None

    def test_get_config_invalid_genealogy(self, test_db):
        """Test avec une généalogie qui n'existe pas."""
        result = get_genealogy_config("NonExistent", test_db)
        assert result is None


class TestUpdateGenealogyConfig:
    """Tests pour update_genealogy_config."""

    def test_create_new_config(self, test_db, sample_genealogy):
        """Test création d'une nouvelle config."""
        config_data = {
            "wizard": "friend",
            "friend": "on",
            "public_if_no_date": "yes"
        }
        
        result = update_genealogy_config("TestFamily", config_data, test_db)
        
        assert result is not None
        assert result.genealogy_id == sample_genealogy.id
        assert result.wizard == "friend"
        assert result.friend == "on"
        assert result.public_if_no_date == "yes"

    def test_update_existing_config(self, test_db, sample_genealogy):
        """Test mise à jour d'une config existante."""
        # Créer une config initiale
        config = GenealogyConfig(
            genealogy_id=sample_genealogy.id,
            wizard="friend"
        )
        test_db.add(config)
        test_db.commit()
        
        # Mettre à jour
        new_data = {"wizard": "off", "friend": "on"}
        result = update_genealogy_config("TestFamily", new_data, test_db)
        
        assert result.wizard == "off"
        assert result.friend == "on"

    def test_update_invalid_genealogy(self, test_db):
        """Test mise à jour avec généalogie inexistante."""
        config_data = {"wizard": "friend"}
        result = update_genealogy_config("NonExistent", config_data, test_db)
        
        assert result is None

    def test_update_with_empty_data(self, test_db, sample_genealogy):
        """Test mise à jour avec données vides."""
        config = GenealogyConfig(genealogy_id=sample_genealogy.id)
        test_db.add(config)
        test_db.commit()
        
        result = update_genealogy_config("TestFamily", {}, test_db)
        assert result is not None

    def test_update_with_invalid_fields(self, test_db, sample_genealogy):
        """Test mise à jour avec champs invalides (ignorés)."""
        config_data = {
            "wizard": "friend",
            "invalid_field": "value",
            "another_invalid": 123
        }
        
        result = update_genealogy_config("TestFamily", config_data, test_db)
        
        assert result is not None
        assert result.wizard == "friend"
        assert not hasattr(result, "invalid_field")

    def test_update_multiple_times(self, test_db, sample_genealogy):
        """Test mises à jour multiples."""
        # Première mise à jour
        result1 = update_genealogy_config("TestFamily", {"wizard": "v1"}, test_db)
        assert result1.wizard == "v1"
        
        # Deuxième mise à jour
        result2 = update_genealogy_config("TestFamily", {"wizard": "v2"}, test_db)
        assert result2.wizard == "v2"
        
        # Vérifier qu'il n'y a qu'une seule config
        configs = test_db.query(GenealogyConfig).filter(
            GenealogyConfig.genealogy_id == sample_genealogy.id
        ).all()
        assert len(configs) == 1


class TestGetServerConfig:
    """Tests pour get_server_config."""

    def test_get_existing_config(self, test_db):
        """Test récupération d'une config serveur existante."""
        # Créer une config
        config = ServerConfig(
            id=1,
            default_lang="fr",
            only="public",
            log="enabled"
        )
        test_db.add(config)
        test_db.commit()
        
        result = get_server_config(test_db)
        
        assert result is not None
        assert result.default_lang == "fr"
        assert result.only == "public"

    def test_get_creates_default_if_missing(self, test_db):
        """Test que get crée une config par défaut si absente."""
        result = get_server_config(test_db)
        
        assert result is not None
        assert result.id == 1
        assert result.default_lang == "fr"

    def test_get_singleton_behavior(self, test_db):
        """Test comportement singleton."""
        result1 = get_server_config(test_db)
        result2 = get_server_config(test_db)
        
        assert result1.id == result2.id
        
        # Vérifier qu'il n'y a qu'une seule config
        all_configs = test_db.query(ServerConfig).all()
        assert len(all_configs) == 1


class TestUpdateServerConfig:
    """Tests pour update_server_config."""

    def test_create_server_config(self, test_db):
        """Test création de la config serveur."""
        config_data = {
            "default_lang": "en",
            "only": "private",
            "log": "debug"
        }
        
        result = update_server_config(config_data, test_db)
        
        assert result is not None
        assert result.default_lang == "en"
        assert result.only == "private"
        assert result.log == "debug"

    def test_update_existing_server_config(self, test_db):
        """Test mise à jour de la config existante."""
        # Créer une config initiale
        config = ServerConfig(id=1, default_lang="fr")
        test_db.add(config)
        test_db.commit()
        
        # Mettre à jour
        new_data = {"default_lang": "en", "log": "info"}
        result = update_server_config(new_data, test_db)
        
        assert result.default_lang == "en"
        assert result.log == "info"

    def test_update_with_empty_data(self, test_db):
        """Test mise à jour avec données vides."""
        result = update_server_config({}, test_db)
        assert result is not None

    def test_update_preserves_singleton(self, test_db):
        """Test que update ne crée qu'une seule config."""
        update_server_config({"default_lang": "fr"}, test_db)
        update_server_config({"default_lang": "en"}, test_db)
        update_server_config({"default_lang": "de"}, test_db)
        
        all_configs = test_db.query(ServerConfig).all()
        assert len(all_configs) == 1
        assert all_configs[0].default_lang == "de"


class TestConfigServicesIntegration:
    """Tests d'intégration des services de configuration."""

    def test_multiple_genealogies_configs(self, test_db):
        """Test plusieurs généalogies avec configs différentes."""
        # Créer plusieurs généalogies
        gen1 = Genealogy(name="Family1")
        gen2 = Genealogy(name="Family2")
        test_db.add(gen1)
        test_db.add(gen2)
        test_db.commit()
        
        # Créer des configs différentes
        config1_data = {"wizard": "friend", "friend": "on"}
        config2_data = {"wizard": "off", "friend": "off"}
        
        result1 = update_genealogy_config("Family1", config1_data, test_db)
        result2 = update_genealogy_config("Family2", config2_data, test_db)
        
        assert result1.wizard == "friend"
        assert result2.wizard == "off"
        
        # Vérifier indépendance
        assert result1.genealogy_id != result2.genealogy_id

    def test_genealogy_and_server_configs_coexist(self, test_db, sample_genealogy):
        """Test que configs généalogie et serveur coexistent."""
        # Config généalogie
        gen_config = update_genealogy_config(
            "TestFamily",
            {"wizard": "friend"},
            test_db
        )
        
        # Config serveur
        server_config = update_server_config(
            {"default_lang": "en"},
            test_db
        )
        
        assert gen_config is not None
        assert server_config is not None
        assert gen_config.wizard == "friend"
        assert server_config.default_lang == "en"

    def test_config_persistence(self, test_db, sample_genealogy):
        """Test que les configs persistent après commit."""
        # Créer une config
        update_genealogy_config("TestFamily", {"wizard": "friend"}, test_db)
        
        # Récupérer à nouveau
        result = get_genealogy_config("TestFamily", test_db)
        
        assert result is not None
        assert result.wizard == "friend"

    def test_update_partial_config(self, test_db, sample_genealogy):
        """Test mise à jour partielle de config."""
        # Créer config complète
        initial_data = {
            "wizard": "friend",
            "friend": "on",
            "public_if_no_date": "yes"
        }
        update_genealogy_config("TestFamily", initial_data, test_db)
        
        # Mise à jour partielle
        partial_data = {"wizard": "off"}
        result = update_genealogy_config("TestFamily", partial_data, test_db)
        
        # wizard devrait être mis à jour
        assert result.wizard == "off"
        # friend devrait rester inchangé
        assert result.friend == "on"


class TestConfigServicesEdgeCases:
    """Tests des cas limites pour les services de config."""

    def test_config_with_none_values(self, test_db, sample_genealogy):
        """Test config avec valeurs None."""
        config_data = {
            "wizard": None,
            "friend": None
        }
        
        result = update_genealogy_config("TestFamily", config_data, test_db)
        
        assert result is not None
        assert result.wizard is None
        assert result.friend is None

    def test_config_with_special_characters(self, test_db):
        """Test généalogie avec caractères spéciaux dans le nom."""
        gen = Genealogy(name="Family-2024_Test")
        test_db.add(gen)
        test_db.commit()
        
        config_data = {"wizard": "friend"}
        result = update_genealogy_config("Family-2024_Test", config_data, test_db)
        
        assert result is not None
        assert result.wizard == "friend"

    def test_get_config_after_genealogy_deleted(self, test_db, sample_genealogy):
        """Test récupération config après suppression généalogie."""
        # Créer une config
        update_genealogy_config("TestFamily", {"wizard": "friend"}, test_db)
        
        # Supprimer la généalogie
        test_db.delete(sample_genealogy)
        test_db.commit()
        
        # Essayer de récupérer la config
        result = get_genealogy_config("TestFamily", test_db)
        assert result is None

    def test_concurrent_updates_same_config(self, test_db, sample_genealogy):
        """Test mises à jour concurrentes de la même config."""
        # Créer config initiale
        update_genealogy_config("TestFamily", {"wizard": "v1"}, test_db)
        
        # Plusieurs mises à jour rapides
        for i in range(10):
            update_genealogy_config("TestFamily", {"wizard": f"v{i}"}, test_db)
        
        # Vérifier état final
        result = get_genealogy_config("TestFamily", test_db)
        assert result.wizard == "v9"
        
        # Vérifier qu'il n'y a qu'une seule config
        all_configs = test_db.query(GenealogyConfig).filter(
            GenealogyConfig.genealogy_id == sample_genealogy.id
        ).all()
        assert len(all_configs) == 1
