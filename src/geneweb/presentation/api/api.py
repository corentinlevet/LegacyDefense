from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...application.services import GenealogyService
from ...infrastructure.database import SessionLocal
from ...infrastructure.models import Genealogy

router = APIRouter(prefix="/api")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateGenealogyRequest(BaseModel):
    name: str
    force: bool = False


class GenealogyResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy models


router = APIRouter(prefix="/api")


@router.post("/genealogies", status_code=status.HTTP_201_CREATED)
async def create_genealogy_api(
    request: CreateGenealogyRequest,
    service: GenealogyService = Depends(GenealogyService),
):
    try:
        service.create_genealogy(name=request.name, force=request.force)
        return {"message": f"Genealogy '{request.name}' created successfully."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/genealogies", response_model=List[GenealogyResponse])
async def get_all_genealogies_api(
    service: GenealogyService = Depends(GenealogyService),
):
    try:
        genealogies = service.get_all_genealogies()
        return genealogies
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/genealogies/{genealogy_name}/import")
async def import_gedcom_file(
    genealogy_name: str,
    gedcom_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Endpoint API pour importer un fichier GEDCOM dans une généalogie spécifique.
    """
    try:
        # Lire le contenu du fichier
        gedcom_content = await gedcom_file.read()

        # Essayer différents encodages courants pour les fichiers GEDCOM
        encodings = ["utf-8", "utf-8-sig", "windows-1252", "iso-8859-1", "latin1"]
        gedcom_text = None

        for encoding in encodings:
            try:
                gedcom_text = gedcom_content.decode(encoding)
                print(f"Fichier décodé avec succès en {encoding}")
                break
            except (UnicodeDecodeError, AttributeError):
                continue

        if gedcom_text is None:
            raise HTTPException(
                status_code=400,
                detail="Impossible de décoder le fichier GEDCOM. Encodage non supporté.",
            )

        # Appeler le service pour importer le GEDCOM
        service = GenealogyService()
        service.import_gedcom(genealogy_name, gedcom_text, db)

        return {
            "message": f"Fichier GEDCOM importé avec succès dans la généalogie '{genealogy_name}'.",
            "success": True,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de l'importation: {str(e)}"
        )


@router.get("/genealogies/{genealogy_name}/export", response_class=Response)
async def export_gedcom_api(
    genealogy_name: str,
    service: GenealogyService = Depends(GenealogyService),
):
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
        print("Error during GEDCOM export:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    finally:
        db.close()
