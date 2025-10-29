from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from .. import models


class SQLGenealogyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> models.Genealogy | None:
        result = self.db.execute(
            select(models.Genealogy).filter(models.Genealogy.name == name)
        )
        return result.scalars().first()

    def count_persons(self, genealogy_id: int) -> int:
        result = self.db.execute(
            select(func.count(models.Person.id)).filter(
                models.Person.genealogy_id == genealogy_id
            )
        )
        return result.scalar_one() or 0
