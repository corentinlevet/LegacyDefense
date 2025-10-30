"""
API endpoints for managing genealogies.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...application import config_services
from ...application.services import GenealogyService
from ...infrastructure.database import SessionLocal
from ...infrastructure.models import Genealogy
from ..dependencies import get_db

router = APIRouter(
    tags=["Genealogies"],
)


# Pydantic Models from api.py
class CreateGenealogyRequest(BaseModel):
    name: str
    force: bool = False


class GenealogyResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


# Pydantic Models from config_api.py
class GenealogyConfigRequest(BaseModel):
    body_prop: Optional[str] = None
    default_lang: Optional[str] = None
    trailer: Optional[str] = None
    max_anc_level: Optional[int] = None
    max_desc_level: Optional[int] = None
    max_anc_tree: Optional[int] = None
    max_desc_tree: Optional[int] = None
    history: Optional[bool] = None
    hide_advanced_request: Optional[bool] = None
    images_path: Optional[str] = None
    friend_passwd: Optional[str] = None
    wizard_passwd: Optional[str] = None
    wizard_just_friend: Optional[bool] = None
    hide_private_names: Optional[bool] = None
    can_send_image: Optional[bool] = None
    renamed: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a new genealogy")
async def create_genealogy_api(
    request: CreateGenealogyRequest,
    service: GenealogyService = Depends(GenealogyService),
):
    """
    Creates a new genealogy.

    - **name**: The name of the genealogy.
    - **force**: If true, deletes any existing genealogy with the same name before creating a new one.
    """
    try:
        service.create_genealogy(name=request.name, force=request.force)
        return {"message": f"Genealogy '{request.name}' created successfully."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[GenealogyResponse], summary="List all genealogies")
async def get_all_genealogies_api(
    service: GenealogyService = Depends(GenealogyService),
):
    """
    Retrieves a list of all available genealogies.
    """
    try:
        genealogies = service.get_all_genealogies()
        return genealogies
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{genealogy_name}/import", summary="Import a GEDCOM file")
async def import_gedcom_file(
    genealogy_name: str,
    gedcom_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Imports a GEDCOM file into a specific genealogy.
    The server will attempt to decode the file using various common encodings.
    """
    try:
        gedcom_content = await gedcom_file.read()
        encodings = ["utf-8", "utf-8-sig", "windows-1252", "iso-8859-1", "latin1"]
        gedcom_text = None

        for encoding in encodings:
            try:
                gedcom_text = gedcom_content.decode(encoding)
                break
            except (UnicodeDecodeError, AttributeError):
                continue

        if gedcom_text is None:
            raise HTTPException(
                status_code=400,
                detail="Unable to decode GEDCOM file. Unsupported encoding.",
            )

        service = GenealogyService()
        service.import_gedcom(genealogy_name, gedcom_text, db)

        return {
            "message": f"GEDCOM file imported successfully into genealogy '{genealogy_name}'.",
            "success": True,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during import: {str(e)}")


@router.get(
    "/{genealogy_name}/export",
    response_class=Response,
    summary="Export a genealogy to GEDCOM",
)
async def export_gedcom_api(
    genealogy_name: str,
    service: GenealogyService = Depends(GenealogyService),
):
    """
    Exports a genealogy to a GEDCOM 5.5.1 file.
    """
    db: Session = SessionLocal()
    try:
        genealogy = db.query(Genealogy).filter(Genealogy.name == genealogy_name).first()

        if not genealogy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Genealogy '{genealogy_name}' not found.",
            )

        gedcom_content = service.export_gedcom(genealogy.id, db)

        response = Response(content=gedcom_content, media_type="application/x-gedcom")
        response.headers["Content-Disposition"] = (
            f"attachment; filename={genealogy_name}.ged"
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    finally:
        db.close()


@router.get("/{name}/config", summary="Get genealogy configuration")
def get_genealogy_config_api(name: str, db: Session = Depends(get_db)):
    """
    Retrieves the configuration for a specific genealogy.
    If no specific configuration is found, returns default values.
    """
    config = config_services.get_genealogy_config(name, db)
    if config is None:
        return {
            "body_prop": "",
            "default_lang": "fr",
            "trailer": "",
            "max_anc_level": 12,
            "max_desc_level": 12,
            "max_anc_tree": 7,
            "max_desc_tree": 4,
            "history": True,
            "hide_advanced_request": False,
            "images_path": "",
            "friend_passwd": "",
            "wizard_passwd": "",
            "wizard_just_friend": False,
            "hide_private_names": False,
            "can_send_image": True,
            "renamed": "",
        }

    return {
        "body_prop": config.body_prop or "",
        "default_lang": config.default_lang or "fr",
        "trailer": config.trailer or "",
        "max_anc_level": config.max_anc_level or 12,
        "max_desc_level": config.max_desc_level or 12,
        "max_anc_tree": config.max_anc_tree or 7,
        "max_desc_tree": config.max_desc_tree or 4,
        "history": config.history if config.history is not None else True,
        "hide_advanced_request": (
            config.hide_advanced_request
            if config.hide_advanced_request is not None
            else False
        ),
        "images_path": config.images_path or "",
        "friend_passwd": config.friend_passwd or "",
        "wizard_passwd": config.wizard_passwd or "",
        "wizard_just_friend": (
            config.wizard_just_friend
            if config.wizard_just_friend is not None
            else False
        ),
        "hide_private_names": (
            config.hide_private_names
            if config.hide_private_names is not None
            else False
        ),
        "can_send_image": (
            config.can_send_image if config.can_send_image is not None else True
        ),
        "renamed": config.renamed or "",
    }


@router.put("/{name}/config", summary="Update genealogy configuration")
def update_genealogy_config_api(
    name: str,
    config_data: GenealogyConfigRequest,
    db: Session = Depends(get_db),
):
    """
    Creates or updates the configuration for a specific genealogy.
    Only non-null values from the request will be updated.
    """
    data_dict = {k: v for k, v in config_data.model_dump().items() if v is not None}

    config = config_services.update_genealogy_config(name, data_dict, db)
    if config is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return {"message": "Configuration updated successfully"}
