"""
Repository implementations following the Repository Pattern.

Concrete implementations of the repository interfaces defined in protocols.py,
using SQLAlchemy for database operations. This provides a clean separation
between business logic and data access.

Architecture: Clean Architecture + Repository Pattern
- Domain models (models.py)
- Repository interfaces (protocols.py)  
- Repository implementations (this file)
- Database ORM (database.py)
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from .database import EventORM, FamilyORM, PersonORM
from .models import Event, EventType, Family, Person, Sex


class SQLPersonRepository:
    """
    SQLAlchemy implementation of PersonRepository.
    
    Handles all database operations for Person entities.
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def find_by_id(self, person_id: int) -> Optional[Person]:
        """
        Retrieve a person by their unique identifier.
        
        Args:
            person_id: Unique identifier of the person
            
        Returns:
            Person object if found, None otherwise
        """
        person_orm = (
            self.session.query(PersonORM)
            .filter(PersonORM.id == person_id)
            .first()
        )

        if not person_orm:
            return None

        return self._orm_to_model(person_orm)

    def find_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Person]:
        """
        Retrieve all persons with optional pagination.
        
        Args:
            limit: Maximum number of persons to return
            offset: Number of persons to skip
            
        Returns:
            List of Person objects
        """
        query = self.session.query(PersonORM).offset(offset)

        if limit:
            query = query.limit(limit)

        persons_orm = query.all()
        return [self._orm_to_model(p) for p in persons_orm]

    def find_by_name(
        self,
        first_name: Optional[str] = None,
        surname: Optional[str] = None,
    ) -> List[Person]:
        """
        Find persons by name (partial match supported).
        
        Args:
            first_name: First name to search for (optional)
            surname: Surname to search for (optional)
            
        Returns:
            List of matching Person objects
        """
        query = self.session.query(PersonORM)

        if first_name:
            query = query.filter(
                PersonORM.first_name.ilike(f"%{first_name}%")
            )

        if surname:
            query = query.filter(
                PersonORM.surname.ilike(f"%{surname}%")
            )

        persons_orm = query.all()
        return [self._orm_to_model(p) for p in persons_orm]

    def save(self, person: Person) -> int:
        """
        Save a person (create or update).
        
        Args:
            person: Person object to save
            
        Returns:
            ID of the saved person
        """
        if person.id:
            # Update existing
            person_orm = (
                self.session.query(PersonORM)
                .filter(PersonORM.id == person.id)
                .first()
            )
            if person_orm:
                self._update_orm_from_model(person_orm, person)
            else:
                # ID provided but doesn't exist, create new
                person_orm = self._model_to_orm(person)
                self.session.add(person_orm)
        else:
            # Create new
            person_orm = self._model_to_orm(person)
            self.session.add(person_orm)

        self.session.flush()
        return person_orm.id

    def delete(self, person_id: int) -> bool:
        """
        Delete a person by ID.
        
        Args:
            person_id: ID of person to delete
            
        Returns:
            True if deleted, False if not found
        """
        person_orm = (
            self.session.query(PersonORM)
            .filter(PersonORM.id == person_id)
            .first()
        )

        if not person_orm:
            return False

        self.session.delete(person_orm)
        self.session.flush()
        return True

    def _orm_to_model(self, person_orm: PersonORM) -> Person:
        """Convert ORM entity to domain model."""
        # NOTE: This is a simplified conversion
        # In production, would handle all fields and relationships
        return Person(
            id=person_orm.id,
            first_name=person_orm.first_name,
            surname=person_orm.surname,
            sex=person_orm.sex,
            occupation=person_orm.occupation,
            notes=person_orm.notes,
            consang=person_orm.consang,
        )

    def _model_to_orm(self, person: Person) -> PersonORM:
        """Convert domain model to ORM entity."""
        person_orm = PersonORM(
            first_name=person.first_name,
            surname=person.surname,
            sex=person.sex,
            occupation=person.occupation,
            notes=person.notes,
            consang=person.consang,
        )

        if person.id:
            person_orm.id = person.id

        return person_orm

    def _update_orm_from_model(
        self, person_orm: PersonORM, person: Person
    ) -> None:
        """Update ORM entity from domain model."""
        person_orm.first_name = person.first_name
        person_orm.surname = person.surname
        person_orm.sex = person.sex
        person_orm.occupation = person.occupation
        person_orm.notes = person.notes
        person_orm.consang = person.consang


class SQLFamilyRepository:
    """
    SQLAlchemy implementation of FamilyRepository.
    
    Handles all database operations for Family entities.
    """

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def find_by_id(self, family_id: int) -> Optional[Family]:
        """Retrieve a family by ID."""
        family_orm = (
            self.session.query(FamilyORM)
            .filter(FamilyORM.id == family_id)
            .first()
        )

        if not family_orm:
            return None

        return self._orm_to_model(family_orm)

    def find_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Family]:
        """Retrieve all families with pagination."""
        query = self.session.query(FamilyORM).offset(offset)

        if limit:
            query = query.limit(limit)

        families_orm = query.all()
        return [self._orm_to_model(f) for f in families_orm]

    def find_by_parent(self, parent_id: int) -> List[Family]:
        """Find all families where person is a parent."""
        families_orm = (
            self.session.query(FamilyORM)
            .filter(
                (FamilyORM.father_id == parent_id)
                | (FamilyORM.mother_id == parent_id)
            )
            .all()
        )

        return [self._orm_to_model(f) for f in families_orm]

    def find_by_child(self, child_id: int) -> Optional[Family]:
        """Find family where person is a child."""
        # Find person's parent family
        person_orm = (
            self.session.query(PersonORM)
            .filter(PersonORM.id == child_id)
            .first()
        )

        if not person_orm or not person_orm.parent_family:
            return None

        return self._orm_to_model(person_orm.parent_family)

    def save(self, family: Family) -> int:
        """Save a family (create or update)."""
        if family.id:
            # Update existing
            family_orm = (
                self.session.query(FamilyORM)
                .filter(FamilyORM.id == family.id)
                .first()
            )
            if family_orm:
                self._update_orm_from_model(family_orm, family)
            else:
                # ID provided but doesn't exist
                family_orm = self._model_to_orm(family)
                self.session.add(family_orm)
        else:
            # Create new
            family_orm = self._model_to_orm(family)
            self.session.add(family_orm)

        self.session.flush()
        return family_orm.id

    def delete(self, family_id: int) -> bool:
        """Delete a family by ID."""
        family_orm = (
            self.session.query(FamilyORM)
            .filter(FamilyORM.id == family_id)
            .first()
        )

        if not family_orm:
            return False

        self.session.delete(family_orm)
        self.session.flush()
        return True

    def _orm_to_model(self, family_orm: FamilyORM) -> Family:
        """Convert ORM entity to domain model."""
        return Family(
            id=family_orm.id,
            father_id=family_orm.father_id,
            mother_id=family_orm.mother_id,
            marriage_date=None,  # Would be loaded from events
            divorce_date=None,
        )

    def _model_to_orm(self, family: Family) -> FamilyORM:
        """Convert domain model to ORM entity."""
        family_orm = FamilyORM(
            father_id=family.father_id,
            mother_id=family.mother_id,
        )

        if family.id:
            family_orm.id = family.id

        return family_orm

    def _update_orm_from_model(
        self, family_orm: FamilyORM, family: Family
    ) -> None:
        """Update ORM entity from domain model."""
        family_orm.father_id = family.father_id
        family_orm.mother_id = family.mother_id


class SQLEventRepository:
    """
    SQLAlchemy implementation of EventRepository.
    
    Handles all database operations for Event entities.
    """

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def find_by_id(self, event_id: int) -> Optional[Event]:
        """Retrieve an event by ID."""
        event_orm = (
            self.session.query(EventORM)
            .filter(EventORM.id == event_id)
            .first()
        )

        if not event_orm:
            return None

        return self._orm_to_model(event_orm)

    def find_by_person(self, person_id: int) -> List[Event]:
        """Find all events for a person."""
        # NOTE: This would need to query based on event type
        # For now, simplified implementation
        events_orm = (
            self.session.query(EventORM)
            .filter(
                (EventORM.birth_person_id == person_id)
                | (EventORM.death_person_id == person_id)
                | (EventORM.burial_person_id == person_id)
            )
            .all()
        )

        return [self._orm_to_model(e) for e in events_orm]

    def find_by_family(self, family_id: int) -> List[Event]:
        """Find all events for a family."""
        # Would query marriage/divorce events
        events_orm = (
            self.session.query(EventORM)
            .filter(EventORM.family_id == family_id)
            .all()
        )

        return [self._orm_to_model(e) for e in events_orm]

    def save(self, event: Event) -> int:
        """Save an event (create or update)."""
        # NOTE: Simplified - full implementation would handle
        # all event types and relationships
        event_orm = EventORM()

        self.session.add(event_orm)
        self.session.flush()
        return event_orm.id

    def delete(self, event_id: int) -> bool:
        """Delete an event by ID."""
        event_orm = (
            self.session.query(EventORM)
            .filter(EventORM.id == event_id)
            .first()
        )

        if not event_orm:
            return False

        self.session.delete(event_orm)
        self.session.flush()
        return True

    def _orm_to_model(self, event_orm: EventORM) -> Event:
        """Convert ORM entity to domain model."""
        # Determine event type
        event_type = EventType.BIRTH  # Default

        if event_orm.birth_person_id:
            event_type = EventType.BIRTH
        elif event_orm.death_person_id:
            event_type = EventType.DEATH
        elif event_orm.burial_person_id:
            event_type = EventType.BURIAL

        return Event(
            event_type=event_type,
            date=event_orm.date,
            place=event_orm.place,
            note="",
        )


class RepositoryFactory:
    """
    Factory for creating repository instances.
    
    Provides a centralized way to create repositories with
    proper dependency injection.
    """

    def __init__(self, session: Session):
        """
        Initialize factory with database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create_person_repository(self) -> SQLPersonRepository:
        """Create a PersonRepository instance."""
        return SQLPersonRepository(self.session)

    def create_family_repository(self) -> SQLFamilyRepository:
        """Create a FamilyRepository instance."""
        return SQLFamilyRepository(self.session)

    def create_event_repository(self) -> SQLEventRepository:
        """Create an EventRepository instance."""
        return SQLEventRepository(self.session)


# Convenience functions for quick access
def get_person_repository(session: Session) -> SQLPersonRepository:
    """Get a PersonRepository instance."""
    return SQLPersonRepository(session)


def get_family_repository(session: Session) -> SQLFamilyRepository:
    """Get a FamilyRepository instance."""
    return SQLFamilyRepository(session)


def get_event_repository(session: Session) -> SQLEventRepository:
    """Get an EventRepository instance."""
    return SQLEventRepository(session)
