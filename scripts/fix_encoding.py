import os
import sys

from sqlalchemy.orm import Session

from src.geneweb.infrastructure.database import SessionLocal
from src.geneweb.infrastructure.models import Family, Person

# Ajoute le répertoire parent au path pour que les imports fonctionnent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def fix_string(s: str | None) -> str | None:
    """
    Corrige une chaîne de caractères qui a été mal encodée.
    Exemple : "PyrÃ©nÃ©es" -> "Pyrénées"
    """
    if s is None:
        return None
    try:
        # Tente d'inverser l'encodage incorrect
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Si la chaîne est déjà correcte ou a un autre problème, on ne la touche pas
        return s


def fix_database_encoding(db: Session):
    """
    Parcourt les tables Person et Family pour corriger l'encodage des champs texte.
    """
    print("Début de la correction de l'encodage...")

    # --- Correction de la table Person ---
    print("Correction de la table 'Person'...")
    persons = db.query(Person).all()
    for person in persons:
        person.first_name = fix_string(person.first_name)
        person.surname = fix_string(person.surname)
        person.birth_place = fix_string(person.birth_place)
        person.death_place = fix_string(person.death_place)
        person.baptism_place = fix_string(person.baptism_place)
        person.burial_place = fix_string(person.burial_place)
        person.occupation = fix_string(person.occupation)
        person.notes = fix_string(person.notes)

    print(f"{len(persons)} personnes traitées.")

    # --- Correction de la table Family ---
    print("Correction de la table 'Family'...")
    families = db.query(Family).all()
    for family in families:
        family.marriage_place = fix_string(family.marriage_place)
        family.marriage_note = fix_string(family.marriage_note)

    print(f"{len(families)} familles traitées.")

    # --- Sauvegarde des changements ---
    try:
        print("Sauvegarde des modifications dans la base de données...")
        db.commit()
        print("Correction terminée avec succès !")
    except Exception as e:
        print(f"Une erreur est survenue lors de la sauvegarde : {e}")
        print("Annulation des modifications.")
        db.rollback()


if __name__ == "__main__":
    # Crée une session de base de données
    db_session = SessionLocal()
    try:
        fix_database_encoding(db_session)
    finally:
        # Ferme la session
        db_session.close()
