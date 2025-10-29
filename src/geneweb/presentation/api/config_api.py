"""
API de configuration pour GeneWeb.
Ces endpoints sont ADDITIONNELS et n'altèrent pas l'API existante.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...application import config_services
from ..dependencies import get_db

router = APIRouter(prefix="/api", tags=["configuration"])


# Modèles Pydantic pour les requêtes
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


class ServerConfigRequest(BaseModel):
    default_lang: Optional[str] = None
    only: Optional[str] = None
    log: Optional[str] = None


@router.get("/genealogies/{name}/config")
def get_genealogy_config_api(name: str, db: Session = Depends(get_db)):
    """Récupère la configuration d'une généalogie."""
    config = config_services.get_genealogy_config(name, db)
    if config is None:
        # Retourner des valeurs par défaut si pas de config
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


@router.put("/genealogies/{name}/config")
def update_genealogy_config_api(
    name: str,
    config_data: GenealogyConfigRequest,
    db: Session = Depends(get_db),
):
    """Met à jour la configuration d'une généalogie."""
    # Filtrer les valeurs None
    data_dict = {k: v for k, v in config_data.model_dump().items() if v is not None}

    config = config_services.update_genealogy_config(name, data_dict, db)
    if config is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return {"message": "Configuration updated successfully"}


@router.get("/server/config")
def get_server_config_api(db: Session = Depends(get_db)):
    """Récupère la configuration du serveur."""
    config = config_services.get_server_config(db)
    return {
        "default_lang": config.default_lang or "fr",
        "only": config.only or "",
        "log": config.log or "",
    }


@router.put("/server/config")
def update_server_config_api(
    config_data: ServerConfigRequest, db: Session = Depends(get_db)
):
    """Met à jour la configuration du serveur."""
    # Filtrer les valeurs None
    data_dict = {k: v for k, v in config_data.model_dump().items() if v is not None}

    config_services.update_server_config(data_dict, db)
    return {"message": "Server configuration updated successfully"}
