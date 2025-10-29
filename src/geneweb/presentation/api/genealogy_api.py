from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...application import GenealogyService


class CreateGenealogyRequest(BaseModel):
    name: str
    force: bool = False


class GenealogyResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy models


router = APIRouter()


@router.post("/api/genealogies", status_code=status.HTTP_201_CREATED)
async def create_genealogy_api(
    request: CreateGenealogyRequest,
    service: GenealogyService = Depends(GenealogyService),
):
    try:
        service.create_genealogy(name=request.name, force=request.force)
        return {"message": f"Genealogy '{request.name}' created successfully."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/api/genealogies", response_model=List[GenealogyResponse])
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
