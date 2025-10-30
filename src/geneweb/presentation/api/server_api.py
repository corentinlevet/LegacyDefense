"""
API endpoints for server configuration.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...application import config_services
from ..dependencies import get_db

router = APIRouter(
    tags=["Server"],
)


# Pydantic Models
class ServerConfigRequest(BaseModel):
    default_lang: Optional[str] = None
    only: Optional[str] = None
    log: Optional[str] = None


@router.get("/config", summary="Get server configuration")
def get_server_config_api(db: Session = Depends(get_db)):
    """
    Retrieves the global server configuration.
    If no configuration exists, a default one is created and returned.
    """
    config = config_services.get_server_config(db)
    return {
        "default_lang": config.default_lang or "fr",
        "only": config.only or "",
        "log": config.log or "",
    }


@router.put("/config", summary="Update server configuration")
def update_server_config_api(
    config_data: ServerConfigRequest, db: Session = Depends(get_db)
):
    """
    Updates the global server configuration.
    Only non-null values from the request will be updated.
    """
    data_dict = {k: v for k, v in config_data.model_dump().items() if v is not None}

    config_services.update_server_config(data_dict, db)
    return {"message": "Server configuration updated successfully"}
