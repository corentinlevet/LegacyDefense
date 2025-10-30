"""
Tests pour le service GenealogyService.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from src.geneweb.infrastructure.database import Base
from src.geneweb.infrastructure.models import Genealogy, Person
from src.geneweb.application.services import GenealogyService


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
def genealogy_service():
    """Crée une instance du service de généalogie."""
    return GenealogyService()


class TestCreateGenealogy:
    """Tests pour la méthode create_genealogy."""

    @patch('src.geneweb.application.services.SessionLocal')
    def test_create_new_genealogy(self, mock_session_local, test_db):
        """Test création d'une nouvelle généalogie."""
        mock_session_local.return_value = test_db
        
        service = GenealogyService()
        result = service.create_genealogy("NewFamily")
        
        assert result is not None
        assert result.name == "NewFamily"
        
        # Vérifier dans la DB
        gen = test_db.query(Genealogy).filter(Genealogy.name == "NewFamily").first()
        assert gen is not None

    @patch('src.geneweb.application.services.SessionLocal')
    def test_create_genealogy_already_exists_no_force(self, mock_session_local, test_db):
        """Test création avec nom existant sans force."""
        mock_session_local.return_value = test_db
        
        # Créer une généalogie existante
        existing = Genealogy(name="Existing")
        test_db.add(existing)
        test_db.commit()
        
        service = GenealogyService()
        result = service.create_genealogy("Existing", force=False)
        
        # Ne devrait rien retourner
        assert result is None

    @patch('src.geneweb.application.services.SessionLocal')
    def test_create_genealogy_with_force(self, mock_session_local, test_db):
        """Test création avec force (écrase l'existante)."""
        mock_session_local.return_value = test_db
        
        # Créer une généalogie existante avec des personnes
        existing = Genealogy(name="ToReplace")
        test_db.add(existing)
        test_db.commit()
        
        person = Person(
            genealogy_id=existing.id,
            first_name="Old",
            surname="Person",
            sex="M"
        )
        test_db.add(person)
        test_db.commit()
        
        old_id = existing.id
        
        service = GenealogyService()
        result = service.create_genealogy("ToReplace", force=True)
        
        assert result is not None
        assert result.name == "ToReplace"
        assert result.id != old_id  # Nouvelle ID
        
        # Vérifier que l'ancienne est supprimée
        old_gen = test_db.query(Genealogy).filter(Genealogy.id == old_id).first()
        assert old_gen is None

    @patch('src.geneweb.application.services.SessionLocal')
    def test_create_genealogy_with_special_name(self, mock_session_local, test_db):
        """Test création avec nom spécial."""
        mock_session_local.return_value = test_db
        
        special_names = [
            "Family-2024",
            "O'Connor_Family",
            "Müller Genealogy",
            "Smith & Jones"
        ]
        
        service = GenealogyService()
        
        for name in special_names:
            result = service.create_genealogy(name)
            assert result is not None
            assert result.name == name


class TestGetAllGenealogies:
    """Tests pour la méthode get_all_genealogies."""

    @patch('src.geneweb.application.services.SessionLocal')
    def test_get_all_empty(self, mock_session_local, test_db):
        """Test récupération quand il n'y a aucune généalogie."""
        mock_session_local.return_value = test_db
        
        service = GenealogyService()
        result = service.get_all_genealogies()
        
        assert result == []

    @patch('src.geneweb.application.services.SessionLocal')
    def test_get_all_single(self, mock_session_local, test_db):
        """Test récupération d'une seule généalogie."""
        mock_session_local.return_value = test_db
        
        gen = Genealogy(name="Single")
        test_db.add(gen)
        test_db.commit()
        
        service = GenealogyService()
        result = service.get_all_genealogies()
        
        assert len(result) == 1
        assert result[0].name == "Single"

    @patch('src.geneweb.application.services.SessionLocal')
    def test_get_all_multiple(self, mock_session_local, test_db):
        """Test récupération de plusieurs généalogies."""
        mock_session_local.return_value = test_db
        
        for i in range(5):
            gen = Genealogy(name=f"Family{i}")
            test_db.add(gen)
        test_db.commit()
        
        service = GenealogyService()
        result = service.get_all_genealogies()
        
        assert len(result) == 5
        names = [g.name for g in result]
        assert "Family0" in names
        assert "Family4" in names


class TestImportGedcom:
    """Tests pour la méthode import_gedcom."""

    @patch('src.geneweb.application.services.SessionLocal')
    def test_import_genealogy_not_found(self, mock_session_local, test_db):
        """Test import avec généalogie inexistante."""
        mock_session_local.return_value = test_db
        
        service = GenealogyService()
        
        with pytest.raises(ValueError, match="not found"):
            service.import_gedcom("NonExistent", "fake gedcom", test_db)

    @patch('src.geneweb.application.services.SessionLocal')
    @patch('src.geneweb.application.services.GedcomParser')
    def test_import_basic_gedcom(self, mock_parser, mock_session_local, test_db):
        """Test import basique d'un GEDCOM."""
        mock_session_local.return_value = test_db
        
        # Créer une généalogie
        gen = Genealogy(name="TestImport")
        test_db.add(gen)
        test_db.commit()
        
        # Mock du parser
        mock_parser_instance = MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.get_element_dictionary.return_value = {}
        
        service = GenealogyService()
        gedcom_content = "0 HEAD\n1 CHAR UTF-8"
        
        # Ne devrait pas lever d'exception
        service.import_gedcom("TestImport", gedcom_content, test_db)


class TestGenealogyServiceEdgeCases:
    """Tests des cas limites pour GenealogyService."""

    @patch('src.geneweb.application.services.SessionLocal')
    def test_create_empty_name(self, mock_session_local, test_db):
        """Test création avec nom vide."""
        mock_session_local.return_value = test_db
        
        service = GenealogyService()
        result = service.create_genealogy("")
        
        # Devrait créer quand même (nom vide est valide techniquement)
        assert result is not None

    @patch('src.geneweb.application.services.SessionLocal')
    def test_create_very_long_name(self, mock_session_local, test_db):
        """Test création avec nom très long."""
        mock_session_local.return_value = test_db
        
        long_name = "A" * 99  # Limite de 100 dans le modèle
        service = GenealogyService()
        result = service.create_genealogy(long_name)
        
        assert result is not None
        assert result.name == long_name

    @patch('src.geneweb.application.services.SessionLocal')
    def test_delete_and_recreate(self, mock_session_local, test_db):
        """Test suppression puis recréation."""
        mock_session_local.return_value = test_db
        
        service = GenealogyService()
        
        # Créer
        gen1 = service.create_genealogy("TestGen")
        assert gen1 is not None
        
        # Recréer avec force
        gen2 = service.create_genealogy("TestGen", force=True)
        assert gen2 is not None
        assert gen2.id != gen1.id

    @patch('src.geneweb.application.services.SessionLocal')
    def test_multiple_operations_same_session(self, mock_session_local, test_db):
        """Test plusieurs opérations dans la même session."""
        mock_session_local.return_value = test_db
        
        service = GenealogyService()
        
        # Créer plusieurs généalogies
        gen1 = service.create_genealogy("Gen1")
        gen2 = service.create_genealogy("Gen2")
        gen3 = service.create_genealogy("Gen3")
        
        # Récupérer toutes
        all_gen = service.get_all_genealogies()
        
        assert len(all_gen) == 3
        names = [g.name for g in all_gen]
        assert "Gen1" in names
        assert "Gen2" in names
        assert "Gen3" in names
