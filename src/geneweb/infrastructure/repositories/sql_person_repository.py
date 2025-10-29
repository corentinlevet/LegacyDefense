from sqlalchemy.orm import Session

from ..models import Person


class SQLPersonRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_by_id(self, person_id: int):
        return self.db_session.query(Person).filter(Person.id == person_id).first()

    def add(self, person: Person):
        self.db_session.add(person)
        self.db_session.commit()
        self.db_session.refresh(person)
        return person
