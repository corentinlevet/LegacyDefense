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

    def get_first_names(self, genealogy_id: int) -> list[str]:
        result = self.db.execute(
            select(models.Person.first_name)
            .filter(models.Person.genealogy_id == genealogy_id)
            .distinct()
            .order_by(models.Person.first_name)
        )
        return result.scalars().all()

    def get_last_names(self, genealogy_id: int) -> list[str]:
        result = self.db.execute(
            select(models.Person.surname)
            .filter(models.Person.genealogy_id == genealogy_id)
            .distinct()
        )
        return result.scalars().all()

    def get_places(self, genealogy_id: int) -> list[str]:
        person_birth_places = (
            self.db.execute(
                select(models.Person.birth_place)
                .filter(
                    models.Person.genealogy_id == genealogy_id,
                    models.Person.birth_place.isnot(None),
                )
                .distinct()
            )
            .scalars()
            .all()
        )
        person_death_places = (
            self.db.execute(
                select(models.Person.death_place)
                .filter(
                    models.Person.genealogy_id == genealogy_id,
                    models.Person.death_place.isnot(None),
                )
                .distinct()
            )
            .scalars()
            .all()
        )
        person_baptism_places = (
            self.db.execute(
                select(models.Person.baptism_place)
                .filter(
                    models.Person.genealogy_id == genealogy_id,
                    models.Person.baptism_place.isnot(None),
                )
                .distinct()
            )
            .scalars()
            .all()
        )
        person_burial_places = (
            self.db.execute(
                select(models.Person.burial_place)
                .filter(
                    models.Person.genealogy_id == genealogy_id,
                    models.Person.burial_place.isnot(None),
                )
                .distinct()
            )
            .scalars()
            .all()
        )
        family_marriage_places = (
            self.db.execute(
                select(models.Family.marriage_place)
                .filter(
                    models.Family.genealogy_id == genealogy_id,
                    models.Family.marriage_place.isnot(None),
                )
                .distinct()
            )
            .scalars()
            .all()
        )

        all_places = (
            set(person_birth_places)
            | set(person_death_places)
            | set(person_baptism_places)
            | set(person_burial_places)
            | set(family_marriage_places)
        )

        return sorted(list(all_places))

    def get_occupations(self, genealogy_id: int) -> list[str]:
        result = self.db.execute(
            select(models.Person.occupation)
            .filter(
                models.Person.genealogy_id == genealogy_id,
                models.Person.occupation.isnot(None),
            )
            .distinct()
        )
        return result.scalars().all()

    def get_sources(self, genealogy_id: int) -> list[str]:
        event_sources = (
            self.db.execute(
                select(models.Event.source)
                .filter(
                    models.Event.genealogy_id == genealogy_id,
                    models.Event.source.isnot(None),
                )
                .distinct()
            )
            .scalars()
            .all()
        )

        family_sources = (
            self.db.execute(
                select(models.Family.marriage_src)
                .filter(
                    models.Family.genealogy_id == genealogy_id,
                    models.Family.marriage_src.isnot(None),
                )
                .distinct()
            )
            .scalars()
            .all()
        )

        all_sources = set(event_sources) | set(family_sources)

        return sorted(list(all_sources))
