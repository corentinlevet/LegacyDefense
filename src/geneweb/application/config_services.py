"""
Services de configuration pour GeneWeb.
Ces services sont ADDITIONNELS et n'altèrent pas les services existants.
"""

from typing import Dict, Optional

from sqlalchemy.orm import Session

from ..infrastructure.config_models import GenealogyConfig, ServerConfig
from ..infrastructure.models import Genealogy


def get_genealogy_config(genealogy_name: str, db: Session) -> Optional[GenealogyConfig]:
    """Récupère la configuration d'une généalogie."""
    genealogy = db.query(Genealogy).filter(Genealogy.name == genealogy_name).first()
    if not genealogy:
        return None

    config = (
        db.query(GenealogyConfig)
        .filter(GenealogyConfig.genealogy_id == genealogy.id)
        .first()
    )
    return config


def update_genealogy_config(
    genealogy_name: str, config_data: Dict, db: Session
) -> Optional[GenealogyConfig]:
    """Crée ou met à jour la configuration d'une généalogie."""
    genealogy = db.query(Genealogy).filter(Genealogy.name == genealogy_name).first()
    if not genealogy:
        return None

    config = (
        db.query(GenealogyConfig)
        .filter(GenealogyConfig.genealogy_id == genealogy.id)
        .first()
    )

    if not config:
        config = GenealogyConfig(genealogy_id=genealogy.id)
        db.add(config)

    # Mise à jour des champs
    for key, value in config_data.items():
        if hasattr(config, key):
            setattr(config, key, value)

    db.commit()
    db.refresh(config)
    return config


def get_server_config(db: Session) -> ServerConfig:
    """Récupère la configuration du serveur (singleton)."""
    config = db.query(ServerConfig).first()
    if not config:
        # Créer une configuration par défaut
        config = ServerConfig(id=1, default_lang="fr", only="", log="")
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def update_server_config(config_data: Dict, db: Session) -> ServerConfig:
    """Met à jour la configuration du serveur."""
    config = db.query(ServerConfig).first()
    if not config:
        config = ServerConfig(id=1)
        db.add(config)

    # Mise à jour des champs
    for key, value in config_data.items():
        if hasattr(config, key):
            setattr(config, key, value)

    db.commit()
    db.refresh(config)
    return config
