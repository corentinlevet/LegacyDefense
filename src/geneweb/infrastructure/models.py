import enum

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class SexEnum(enum.Enum):
    M = "M"
    F = "F"
    U = "U"  # Unknown


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    surname = Column(String, index=True)
    sex = Column(Enum(SexEnum))
    birth_date = Column(Date)
    death_date = Column(Date)
    father_id = Column(Integer, ForeignKey("persons.id"))
    mother_id = Column(Integer, ForeignKey("persons.id"))

    father = relationship("Person", remote_side=[id], foreign_keys=[father_id])
    mother = relationship("Person", remote_side=[id], foreign_keys=[mother_id])
