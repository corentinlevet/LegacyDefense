import enum

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from .database import Base


class SexEnum(enum.Enum):
    M = "M"
    F = "F"
    U = "U"  # Unknown


class Genealogy(Base):
    __tablename__ = "genealogies"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)

    persons = relationship(
        "Person", back_populates="genealogy", cascade="all, delete-orphan"
    )
    families = relationship(
        "Family", back_populates="genealogy", cascade="all, delete-orphan"
    )
    places = relationship(
        "Place", back_populates="genealogy", cascade="all, delete-orphan"
    )
    events = relationship(
        "Event", back_populates="genealogy", cascade="all, delete-orphan"
    )


family_children = Table(
    "family_children",
    Base.metadata,
    Column("family_id", Integer, ForeignKey("families.id"), primary_key=True),
    Column("person_id", Integer, ForeignKey("persons.id"), primary_key=True),
)


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    genealogy_id = Column(
        Integer, ForeignKey("genealogies.id"), nullable=False, index=True
    )
    first_name = Column(String(100), nullable=False, index=True)
    surname = Column(String(100), nullable=False, index=True)
    sex = Column(String(1))
    birth_date = Column(String(50))
    birth_place = Column(String(200))
    death_date = Column(String(50))
    death_place = Column(String(200))
    occupation = Column(String(200))
    notes = Column(Text)
    public_name = Column(String(100))
    qualifier = Column(String(50))
    alias = Column(String(100))
    image = Column(String(200))
    baptism_date = Column(String(50))
    baptism_place = Column(String(200))
    burial_date = Column(String(50))
    burial_place = Column(String(200))
    access = Column(String(20))

    genealogy = relationship("Genealogy", back_populates="persons")
    events = relationship("Event", back_populates="person")


class Family(Base):
    __tablename__ = "families"

    id = Column(Integer, primary_key=True)
    genealogy_id = Column(
        Integer, ForeignKey("genealogies.id"), nullable=False, index=True
    )
    father_id = Column(Integer, ForeignKey("persons.id"), index=True)
    mother_id = Column(Integer, ForeignKey("persons.id"), index=True)
    marriage_date = Column(String(50))
    marriage_place = Column(String(200))
    divorce_date = Column(String(50))
    marriage_note = Column(Text)
    marriage_src = Column(String(200))

    genealogy = relationship("Genealogy", back_populates="families")
    father = relationship("Person", foreign_keys=[father_id])
    mother = relationship("Person", foreign_keys=[mother_id])
    children = relationship(
        "Person", secondary=family_children, backref="child_of_families"
    )
    events = relationship("Event", back_populates="family")


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True)
    genealogy_id = Column(
        Integer, ForeignKey("genealogies.id"), nullable=False, index=True
    )
    name = Column(String(200), nullable=False, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    country = Column(String(100))
    region = Column(String(100))

    genealogy = relationship("Genealogy", back_populates="places")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    genealogy_id = Column(
        Integer, ForeignKey("genealogies.id"), nullable=False, index=True
    )
    person_id = Column(Integer, ForeignKey("persons.id"), index=True)
    family_id = Column(Integer, ForeignKey("families.id"))
    event_type = Column(String(50), nullable=False, index=True)
    date = Column(String(50))
    place = Column(String(200))
    note = Column(Text)
    source = Column(String(200))

    genealogy = relationship("Genealogy", back_populates="events")
    person = relationship("Person", back_populates="events")
    family = relationship("Family", back_populates="events")
