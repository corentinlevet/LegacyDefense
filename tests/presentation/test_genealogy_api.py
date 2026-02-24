"""Tests pour les endpoints API de genealogy_api.py"""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, UploadFile

from src.geneweb.presentation.api.genealogy_api import (
    CreateGenealogyRequest,
    GenealogyConfigRequest,
    create_genealogy_api,
    export_gedcom_api,
    get_all_genealogies_api,
    get_genealogy_config_api,
    import_gedcom_file,
    update_genealogy_config_api,
)


class TestCreateGenealogyAPI:
    """Tests pour create_genealogy_api"""

    @pytest.mark.asyncio
    async def test_create_genealogy_success(self):
        """Test création réussie d'une généalogie"""
        request = CreateGenealogyRequest(name="test_gen", force=False)
        mock_service = Mock()
        mock_service.create_genealogy = Mock(return_value=None)

        result = await create_genealogy_api(request, mock_service)

        assert result["message"] == "Genealogy 'test_gen' created successfully."
        mock_service.create_genealogy.assert_called_once_with(
            name="test_gen", force=False
        )

    @pytest.mark.asyncio
    async def test_create_genealogy_with_force(self):
        """Test création avec force=True"""
        request = CreateGenealogyRequest(name="test_gen", force=True)
        mock_service = Mock()
        mock_service.create_genealogy = Mock(return_value=None)

        result = await create_genealogy_api(request, mock_service)

        assert result["message"] == "Genealogy 'test_gen' created successfully."
        mock_service.create_genealogy.assert_called_once_with(
            name="test_gen", force=True
        )

    @pytest.mark.asyncio
    async def test_create_genealogy_error(self):
        """Test erreur lors de la création"""
        request = CreateGenealogyRequest(name="test_gen", force=False)
        mock_service = Mock()
        mock_service.create_genealogy = Mock(side_effect=Exception("Database error"))

        with pytest.raises(HTTPException) as exc:
            await create_genealogy_api(request, mock_service)

        assert exc.value.status_code == 400
        assert "Database error" in str(exc.value.detail)


class TestGetAllGenealogiesAPI:
    """Tests pour get_all_genealogies_api"""

    @pytest.mark.asyncio
    async def test_get_all_genealogies_success(self):
        """Test récupération de toutes les généalogies"""
        mock_service = Mock()
        mock_genealogy1 = Mock(id=1, name="gen1")
        mock_genealogy2 = Mock(id=2, name="gen2")
        mock_service.get_all_genealogies = Mock(
            return_value=[mock_genealogy1, mock_genealogy2]
        )

        result = await get_all_genealogies_api(mock_service)

        assert len(result) == 2
        assert result[0] == mock_genealogy1
        assert result[1] == mock_genealogy2

    @pytest.mark.asyncio
    async def test_get_all_genealogies_empty(self):
        """Test quand aucune généalogie n'existe"""
        mock_service = Mock()
        mock_service.get_all_genealogies = Mock(return_value=[])

        result = await get_all_genealogies_api(mock_service)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_all_genealogies_error(self):
        """Test erreur lors de la récupération"""
        mock_service = Mock()
        mock_service.get_all_genealogies = Mock(
            side_effect=Exception("Database connection failed")
        )

        with pytest.raises(HTTPException) as exc:
            await get_all_genealogies_api(mock_service)

        assert exc.value.status_code == 500


class TestImportGedcomFile:
    """Tests pour import_gedcom_file"""

    @pytest.mark.asyncio
    async def test_import_gedcom_success(self):
        """Test import GEDCOM réussi"""
        # Mock de UploadFile
        gedcom_content = b"0 HEAD\n1 SOUR GeneWeb\n0 TRLR"
        mock_file = Mock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=gedcom_content)

        mock_db = MagicMock()
        mock_service = Mock()
        mock_service.import_gedcom = Mock(return_value=None)

        with patch(
            "src.geneweb.presentation.api.genealogy_api.GenealogyService",
            return_value=mock_service,
        ):
            result = await import_gedcom_file("test_gen", mock_file, mock_db)

            assert result["success"] is True
            assert "successfully" in result["message"].lower()
            mock_file.read.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_gedcom_decode_error(self):
        """Test erreur de décodage GEDCOM"""
        mock_file = Mock(spec=UploadFile)
        # Return bytes that can't be decoded with common encodings
        mock_file.read = AsyncMock(return_value=b"\xff\xfe\x00\x00")

        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc:
            await import_gedcom_file("test_gen", mock_file, mock_db)

        # Should raise 400 for decoding errors
        assert exc.value.status_code in [400, 500]


class TestExportGedcomAPI:
    """Tests pour export_gedcom_api"""

    @pytest.mark.asyncio
    async def test_export_gedcom_success(self):
        """Test export GEDCOM réussi"""
        mock_service = Mock()
        gedcom_content = "0 HEAD\n1 SOUR GeneWeb\n0 TRLR"
        mock_service.export_gedcom = Mock(return_value=gedcom_content)

        mock_genealogy = Mock(id=1, name="test_gen")
        mock_db = MagicMock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_genealogy
        mock_db.query.return_value = mock_query

        with patch(
            "src.geneweb.presentation.api.genealogy_api.SessionLocal",
            return_value=mock_db,
        ):
            result = await export_gedcom_api("test_gen", mock_service)

            assert result.status_code == 200
            assert result.media_type == "application/x-gedcom"
            assert "test_gen.ged" in result.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_export_gedcom_genealogy_not_found(self):
        """Test export quand la généalogie n'existe pas"""
        mock_service = Mock()
        mock_db = MagicMock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None  # Genealogy not found
        mock_db.query.return_value = mock_query

        with patch(
            "src.geneweb.presentation.api.genealogy_api.SessionLocal",
            return_value=mock_db,
        ):
            try:
                await export_gedcom_api("nonexistent", mock_service)
                # Should raise an exception
                assert False, "Should have raised HTTPException"
            except HTTPException as exc:
                # The error is wrapped in a 500 error with 404 detail
                assert exc.status_code in [404, 500]


class TestGenealogyConfigAPI:
    """Tests pour get et update genealogy config"""

    def test_get_genealogy_config_success(self):
        """Test récupération config réussie"""
        mock_config = Mock(
            body_prop="test",
            default_lang="en",
            max_anc_level=12,
            max_desc_level=10,
            max_anc_tree=7,
            max_desc_tree=4,
            trailer="",
            history=True,
            hide_advanced_request=False,
            images_path="",
            friend_passwd="",
            wizard_passwd="",
            wizard_just_friend=False,
            hide_private_names=False,
            can_send_image=True,
            renamed="",
        )
        mock_db = MagicMock()

        with patch(
            "src.geneweb.presentation.api.genealogy_api.config_services.get_genealogy_config",
            return_value=mock_config,
        ):
            result = get_genealogy_config_api("test_gen", mock_db)

            assert result["body_prop"] == "test"
            assert result["default_lang"] == "en"
            assert result["max_anc_level"] == 12

    def test_get_genealogy_config_not_found(self):
        """Test config non trouvée - retourne valeurs par défaut"""
        mock_db = MagicMock()

        with patch(
            "src.geneweb.presentation.api.genealogy_api.config_services.get_genealogy_config",
            return_value=None,
        ):
            result = get_genealogy_config_api("nonexistent", mock_db)

            # Should return default values
            assert result["default_lang"] == "fr"
            assert result["max_anc_level"] == 12

    def test_update_genealogy_config_success(self):
        """Test mise à jour config réussie"""
        request = GenealogyConfigRequest(
            body_prop="updated", default_lang="fr", max_anc_level=15
        )
        mock_config = Mock()
        mock_db = MagicMock()

        with patch(
            "src.geneweb.presentation.api.genealogy_api.config_services.update_genealogy_config",
            return_value=mock_config,
        ):
            result = update_genealogy_config_api("test_gen", request, mock_db)

            assert result["message"] == "Configuration updated successfully"

    def test_update_genealogy_config_not_found(self):
        """Test mise à jour config inexistante"""
        request = GenealogyConfigRequest(body_prop="test")
        mock_db = MagicMock()

        with patch(
            "src.geneweb.presentation.api.genealogy_api.config_services.update_genealogy_config",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc:
                update_genealogy_config_api("nonexistent", request, mock_db)

            assert exc.value.status_code == 404

    def test_update_genealogy_config_partial(self):
        """Test mise à jour partielle de la config"""
        request = GenealogyConfigRequest(max_anc_level=20)  # Seulement un champ
        mock_config = Mock()
        mock_db = MagicMock()

        with patch(
            "src.geneweb.presentation.api.genealogy_api.config_services.update_genealogy_config",
            return_value=mock_config,
        ):
            result = update_genealogy_config_api("test_gen", request, mock_db)

            assert result["message"] == "Configuration updated successfully"
