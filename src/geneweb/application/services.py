from sqlalchemy.orm import Session

from ..infrastructure.database import SessionLocal
from ..infrastructure.models import Genealogy


class GenealogyService:
    def create_genealogy(self, name: str, force: bool = False):
        """
        Creates a new genealogy.

        :param name: The name of the genealogy.
        :param force: If True, deletes the existing genealogy and its data.
        """
        db: Session = SessionLocal()
        try:
            existing_genealogy = (
                db.query(Genealogy).filter(Genealogy.name == name).first()
            )

            if existing_genealogy:
                if not force:
                    print(
                        f"Genealogy '{name}' already exists. Use --force to overwrite."
                    )
                    return
                else:
                    print(f"Deleting existing genealogy '{name}'...")
                    db.delete(existing_genealogy)
                    db.commit()  # Commit the deletion

            print(f"Creating new genealogy '{name}'...")
            new_genealogy = Genealogy(name=name)
            db.add(new_genealogy)
            db.commit()
            print(f"Genealogy '{name}' created successfully.")

        finally:
            db.close()

    def get_all_genealogies(self):
        """
        Retrieves all genealogies.
        """
        db: Session = SessionLocal()
        try:
            genealogies = db.query(Genealogy).all()
            return genealogies
        finally:
            db.close()
