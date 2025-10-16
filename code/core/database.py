"""
Database layer for GeneWeb Python implementation using SQLAlchemy.

This module provides ORM models and database operations to replace the
original OCaml binary database format.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                        Index, Integer, String, Table, Text, create_engine)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (Session, declarative_base, relationship,
                            sessionmaker)

from .models import (Calendar, DatePrecision, DeathReason, DivorceType,
                     EventType, MarriageType, RelationType, Sex)

Base = declarative_base()

# Association tables for many-to-many relationships
person_family_children = Table(
    "person_family_children",
    Base.metadata,
    Column("person_id", Integer, ForeignKey("persons.id"), primary_key=True),
    Column("family_id", Integer, ForeignKey("families.id"), primary_key=True),
)

event_witnesses = Table(
    "event_witnesses",
    Base.metadata,
    Column("event_id", Integer, ForeignKey("events.id"), primary_key=True),
    Column("person_id", Integer, ForeignKey("persons.id"), primary_key=True),
)

family_event_witnesses = Table(
    "family_event_witnesses",
    Base.metadata,
    Column(
        "family_event_id", Integer, ForeignKey("family_events.id"), primary_key=True
    ),
    Column("person_id", Integer, ForeignKey("persons.id"), primary_key=True),
)


class PersonORM(Base):
    """SQLAlchemy ORM model for Person."""

    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Name components
    first_name = Column(String(255), nullable=False, default="")
    surname = Column(String(255), nullable=False, default="")
    occ = Column(Integer, default=0)  # Occurrence number
    public_name = Column(String(255), default="")
    qualifiers = Column(Text, default="")  # JSON array as text
    aliases = Column(Text, default="")  # JSON array as text
    first_names_aliases = Column(Text, default="")  # JSON array as text
    surnames_aliases = Column(Text, default="")  # JSON array as text

    # Basic info
    sex = Column(Enum(Sex), default=Sex.NEUTER)
    occupation = Column(Text, default="")
    image = Column(String(500), default="")
    notes = Column(Text, default="")
    psources = Column(Text, default="")

    # Consanguinity
    consang = Column(Float, default=0.0)

    # Access control
    access = Column(String(50), default="iftitles")

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    birth_event = relationship(
        "EventORM",
        foreign_keys="EventORM.birth_person_id",
        back_populates="birth_person",
        uselist=False,
    )
    death_event = relationship(
        "EventORM",
        foreign_keys="EventORM.death_person_id",
        back_populates="death_person",
        uselist=False,
    )
    burial_event = relationship(
        "EventORM",
        foreign_keys="EventORM.burial_person_id",
        back_populates="burial_person",
        uselist=False,
    )

    events = relationship(
        "EventORM", foreign_keys="EventORM.person_id", back_populates="person"
    )
    titles = relationship("TitleORM", back_populates="person")

    # Family relationships
    parent_family_id = Column(Integer, ForeignKey("families.id"), nullable=True)
    parent_family = relationship(
        "FamilyORM", foreign_keys=[parent_family_id], back_populates="children"
    )

    # Spouse relationships
    families_as_father = relationship(
        "FamilyORM", foreign_keys="FamilyORM.father_id", back_populates="father"
    )
    families_as_mother = relationship(
        "FamilyORM", foreign_keys="FamilyORM.mother_id", back_populates="mother"
    )

    # Event witnesses
    witnessed_events = relationship(
        "EventORM", secondary=event_witnesses, back_populates="witnesses"
    )
    witnessed_family_events = relationship(
        "FamilyEventORM", secondary=family_event_witnesses, back_populates="witnesses"
    )

    # Indexes
    __table_args__ = (
        Index("idx_person_surname", "surname"),
        Index("idx_person_first_name", "first_name"),
        Index("idx_person_names", "first_name", "surname"),
        Index("idx_person_sex", "sex"),
    )


class FamilyORM(Base):
    """SQLAlchemy ORM model for Family."""

    __tablename__ = "families"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Parents
    father_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    mother_id = Column(Integer, ForeignKey("persons.id"), nullable=True)

    # Marriage information
    marriage = Column(Enum(MarriageType), default=MarriageType.MARRIED)
    marriage_note = Column(Text, default="")
    marriage_source = Column(Text, default="")

    # Divorce information
    divorce = Column(Enum(DivorceType), default=DivorceType.NOT_DIVORCED)

    # Additional info
    notes = Column(Text, default="")
    fsources = Column(Text, default="")

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    father = relationship(
        "PersonORM", foreign_keys=[father_id], back_populates="families_as_father"
    )
    mother = relationship(
        "PersonORM", foreign_keys=[mother_id], back_populates="families_as_mother"
    )
    children = relationship(
        "PersonORM",
        foreign_keys="PersonORM.parent_family_id",
        back_populates="parent_family",
    )

    events = relationship("FamilyEventORM", back_populates="family")

    # Indexes
    __table_args__ = (
        Index("idx_family_father", "father_id"),
        Index("idx_family_mother", "mother_id"),
        Index("idx_family_parents", "father_id", "mother_id"),
    )


class DateORM(Base):
    """SQLAlchemy ORM model for Date."""

    __tablename__ = "dates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day = Column(Integer, nullable=True)
    month = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    precision = Column(Enum(DatePrecision), default=DatePrecision.SURE)
    calendar = Column(Enum(Calendar), default=Calendar.GREGORIAN)
    delta = Column(Integer, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_date_year", "year"),
        Index("idx_date_full", "year", "month", "day"),
    )


class PlaceORM(Base):
    """SQLAlchemy ORM model for Place."""

    __tablename__ = "places"

    id = Column(Integer, primary_key=True, autoincrement=True)
    place = Column(String(255), default="")
    town = Column(String(255), default="")
    township = Column(String(255), default="")
    county = Column(String(255), default="")
    state = Column(String(255), default="")
    country = Column(String(255), default="")

    # Indexes
    __table_args__ = (
        Index("idx_place_town", "town"),
        Index("idx_place_country", "country"),
        Index("idx_place_location", "town", "country"),
    )


class EventORM(Base):
    """SQLAlchemy ORM model for Event."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(Enum(EventType), nullable=False)
    reason = Column(Text, default="")
    note = Column(Text, default="")
    source = Column(Text, default="")

    # Foreign keys
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    birth_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    death_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    burial_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    date_id = Column(Integer, ForeignKey("dates.id"), nullable=True)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=True)

    # Relationships
    person = relationship(
        "PersonORM", foreign_keys=[person_id], back_populates="events"
    )
    birth_person = relationship(
        "PersonORM", foreign_keys=[birth_person_id], back_populates="birth_event"
    )
    death_person = relationship(
        "PersonORM", foreign_keys=[death_person_id], back_populates="death_event"
    )
    burial_person = relationship(
        "PersonORM", foreign_keys=[burial_person_id], back_populates="burial_event"
    )

    date = relationship("DateORM")
    place = relationship("PlaceORM")
    witnesses = relationship(
        "PersonORM", secondary=event_witnesses, back_populates="witnessed_events"
    )

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Indexes
    __table_args__ = (
        Index("idx_event_person", "person_id"),
        Index("idx_event_type", "event_type"),
        Index("idx_event_date", "date_id"),
    )


class FamilyEventORM(Base):
    """SQLAlchemy ORM model for Family Event."""

    __tablename__ = "family_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)  # FamilyEventType enum
    reason = Column(Text, default="")
    note = Column(Text, default="")
    source = Column(Text, default="")

    # Foreign keys
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False)
    date_id = Column(Integer, ForeignKey("dates.id"), nullable=True)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=True)

    # Relationships
    family = relationship("FamilyORM", back_populates="events")
    date = relationship("DateORM")
    place = relationship("PlaceORM")
    witnesses = relationship(
        "PersonORM",
        secondary=family_event_witnesses,
        back_populates="witnessed_family_events",
    )

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TitleORM(Base):
    """SQLAlchemy ORM model for Title."""

    __tablename__ = "titles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255), default="")
    fief = Column(String(255), default="")
    nth = Column(Integer, nullable=True)

    # Foreign keys
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    date_start_id = Column(Integer, ForeignKey("dates.id"), nullable=True)
    date_end_id = Column(Integer, ForeignKey("dates.id"), nullable=True)

    # Relationships
    person = relationship("PersonORM", back_populates="titles")
    date_start = relationship("DateORM", foreign_keys=[date_start_id])
    date_end = relationship("DateORM", foreign_keys=[date_end_id])


class DatabaseManager:
    """Database manager for GeneWeb operations."""

    def __init__(self, database_url: str = "sqlite:///geneweb.db"):
        """Initialize database manager."""
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def add_person(self, session: Session, person_data: Dict[str, Any]) -> PersonORM:
        """Add a person to the database."""
        person = PersonORM(**person_data)
        session.add(person)
        session.commit()
        session.refresh(person)
        return person

    def add_family(self, session: Session, family_data: Dict[str, Any]) -> FamilyORM:
        """Add a family to the database."""
        family = FamilyORM(**family_data)
        session.add(family)
        session.commit()
        session.refresh(family)
        return family

    def find_persons_by_name(
        self, session: Session, first_name: str = None, surname: str = None
    ) -> List[PersonORM]:
        """Find persons by name."""
        query = session.query(PersonORM)

        if first_name:
            query = query.filter(PersonORM.first_name.ilike(f"%{first_name}%"))
        if surname:
            query = query.filter(PersonORM.surname.ilike(f"%{surname}%"))

        return query.all()

    def get_person_with_family(
        self, session: Session, person_id: int
    ) -> Optional[PersonORM]:
        """Get person with all family relationships loaded."""
        return session.query(PersonORM).filter(PersonORM.id == person_id).first()

    def get_family_with_members(
        self, session: Session, family_id: int
    ) -> Optional[FamilyORM]:
        """Get family with all members loaded."""
        return session.query(FamilyORM).filter(FamilyORM.id == family_id).first()

    def search_persons(
        self, session: Session, search_term: str, limit: int = 50
    ) -> List[PersonORM]:
        """Search persons by name with fuzzy matching."""
        search_pattern = f"%{search_term}%"
        return (
            session.query(PersonORM)
            .filter(
                (PersonORM.first_name.ilike(search_pattern))
                | (PersonORM.surname.ilike(search_pattern))
                | (PersonORM.public_name.ilike(search_pattern))
            )
            .limit(limit)
            .all()
        )

    def get_descendants(
        self, session: Session, person_id: int, max_generations: int = 10
    ) -> List[PersonORM]:
        """Get all descendants of a person up to max_generations."""
        descendants = []
        current_generation = [person_id]

        for generation in range(max_generations):
            if not current_generation:
                break

            next_generation = []

            # Find families where current generation members are parents
            families = (
                session.query(FamilyORM)
                .filter(
                    (FamilyORM.father_id.in_(current_generation))
                    | (FamilyORM.mother_id.in_(current_generation))
                )
                .all()
            )

            # Collect children from these families
            for family in families:
                children = (
                    session.query(PersonORM)
                    .filter(PersonORM.parent_family_id == family.id)
                    .all()
                )

                descendants.extend(children)
                next_generation.extend([child.id for child in children])

            current_generation = next_generation

        return descendants

    def get_ancestors(
        self, session: Session, person_id: int, max_generations: int = 10
    ) -> List[PersonORM]:
        """Get all ancestors of a person up to max_generations."""
        ancestors = []
        current_generation = [person_id]

        for generation in range(max_generations):
            if not current_generation:
                break

            next_generation = []

            # Find parent families for current generation
            persons = (
                session.query(PersonORM)
                .filter(PersonORM.id.in_(current_generation))
                .all()
            )

            for person in persons:
                if person.parent_family:
                    family = person.parent_family
                    if family.father:
                        ancestors.append(family.father)
                        next_generation.append(family.father_id)
                    if family.mother:
                        ancestors.append(family.mother)
                        next_generation.append(family.mother_id)

            current_generation = next_generation

        return ancestors

    def get_statistics(self, session: Session) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}
        stats["total_persons"] = session.query(PersonORM).count()
        stats["total_families"] = session.query(FamilyORM).count()
        stats["males"] = (
            session.query(PersonORM).filter(PersonORM.sex == Sex.MALE).count()
        )
        stats["females"] = (
            session.query(PersonORM).filter(PersonORM.sex == Sex.FEMALE).count()
        )
        stats["unknown_sex"] = (
            session.query(PersonORM).filter(PersonORM.sex == Sex.NEUTER).count()
        )
        stats["total_events"] = session.query(EventORM).count()
        stats["birth_events"] = (
            session.query(EventORM)
            .filter(EventORM.event_type == EventType.BIRTH)
            .count()
        )
        stats["death_events"] = (
            session.query(EventORM)
            .filter(EventORM.event_type == EventType.DEATH)
            .count()
        )

        return stats

    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        # Implementation depends on database type
        # For SQLite, we can copy the file
        # For PostgreSQL, we'd use pg_dump
        try:
            if "sqlite" in str(self.engine.url):
                import shutil

                db_path = str(self.engine.url).replace("sqlite:///", "")
                shutil.copy2(db_path, backup_path)
                return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False

        return False
