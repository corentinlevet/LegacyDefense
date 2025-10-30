"""
Modèles de configuration pour GeneWeb.
Ces modèles sont ADDITIONNELS et n'altèrent pas les modèles existants.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class GenealogyConfig(Base):
    """
    Configuration spécifique à une généalogie.
    Correspond aux paramètres du fichier .gwf de GeneWeb OCaml.
    """

    __tablename__ = "genealogy_configs"

    id = Column(Integer, primary_key=True)
    genealogy_id = Column(
        Integer, ForeignKey("genealogies.id"), nullable=False, unique=True, index=True
    )

    # Apparence
    body_prop = Column(String(255))  # Style CSS du body
    default_lang = Column(String(10), default="fr")  # Langue par défaut
    trailer = Column(Text)  # Texte en pied de page

    # Limites arbres
    max_anc_level = Column(Integer, default=12)  # Limite ascendance
    max_desc_level = Column(Integer, default=12)  # Limite descendance
    max_anc_tree = Column(Integer, default=7)  # Limite arbre ascendants
    max_desc_tree = Column(Integer, default=4)  # Limite arbre descendants

    # Fonctionnalités
    history = Column(Boolean, default=True)  # Historique des modifications
    hide_advanced_request = Column(Boolean, default=False)  # Cacher recherche avancée
    images_path = Column(String(255))  # Chemin des images

    # Sécurité
    friend_passwd = Column(String(255))  # Mot de passe ami
    wizard_passwd = Column(String(255))  # Mot de passe sorcier
    wizard_just_friend = Column(Boolean, default=False)  # Sorcier = ami
    hide_private_names = Column(Boolean, default=False)  # Masquer noms privés
    can_send_image = Column(Boolean, default=True)  # Envoi d'images autorisé

    # Autres
    renamed = Column(String(255))  # Nouveau nom si renommé

    genealogy = relationship("Genealogy")


class ServerConfig(Base):
    """
    Configuration globale du serveur GeneWeb.
    Correspond aux paramètres gwd.arg de GeneWeb OCaml.
    """

    __tablename__ = "server_configs"

    id = Column(Integer, primary_key=True)
    default_lang = Column(String(10), default="fr")  # Langue par défaut du serveur
    only = Column(String(255))  # Restriction IP (ex: "127.0.0.1,192.168.1.0/24")
    log = Column(String(255))  # Fichier de log
