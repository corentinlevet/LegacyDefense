"""
Service layer for genealogical operations.

Provides high-level business logic operations using repositories.
This layer orchestrates multiple repositories and domain logic.

Architecture: Service Layer Pattern
- Coordinates between repositories
- Implements business workflows
- Handles transactions
- Validates business rules
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from .algorithms import GenealogyAlgorithms
from .models import Family, Person
from .relationship import RelationshipDetector, RelationshipPath
from .repositories import (
    get_event_repository,
    get_family_repository,
    get_person_repository,
)
from .sosa import SosaCalculator


class PersonService:
    """
    Service for person-related operations.
    
    Encapsulates business logic for person management.
    """

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.person_repo = get_person_repository(session)
        self.family_repo = get_family_repository(session)
        self.event_repo = get_event_repository(session)

    def get_person_with_details(self, person_id: int) -> Optional[Person]:
        """
        Get person with full details including relationships.
        
        Args:
            person_id: ID of person to retrieve
            
        Returns:
            Person with complete details or None
        """
        person = self.person_repo.find_by_id(person_id)

        if not person:
            return None

        # Could enrich with events, families, etc.
        return person

    def search_persons(
        self,
        first_name: Optional[str] = None,
        surname: Optional[str] = None,
        limit: int = 100,
    ) -> List[Person]:
        """
        Search for persons by name.
        
        Args:
            first_name: First name to search
            surname: Surname to search
            limit: Maximum results to return
            
        Returns:
            List of matching persons
        """
        results = self.person_repo.find_by_name(first_name, surname)
        return results[:limit]

    def create_person(
        self,
        first_name: str,
        surname: str,
        sex: str,
        occupation: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> int:
        """
        Create a new person.
        
        Args:
            first_name: Person's first name
            surname: Person's surname
            sex: Person's sex (M/F/U)
            occupation: Person's occupation
            notes: Additional notes
            
        Returns:
            ID of created person
        """
        person = Person(
            first_name=first_name,
            surname=surname,
            sex=sex,
            occupation=occupation,
            notes=notes,
        )

        person_id = self.person_repo.save(person)
        self.session.commit()
        return person_id

    def update_person(self, person: Person) -> bool:
        """
        Update an existing person.
        
        Args:
            person: Person object with updated data
            
        Returns:
            True if successful
        """
        if not person.id:
            return False

        self.person_repo.save(person)
        self.session.commit()
        return True

    def delete_person(self, person_id: int) -> bool:
        """
        Delete a person.
        
        Args:
            person_id: ID of person to delete
            
        Returns:
            True if successful
        """
        success = self.person_repo.delete(person_id)

        if success:
            self.session.commit()

        return success


class FamilyService:
    """
    Service for family-related operations.
    
    Manages family creation, updates, and queries.
    """

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.family_repo = get_family_repository(session)
        self.person_repo = get_person_repository(session)

    def get_family_members(
        self, family_id: int
    ) -> Optional[dict[str, Optional[Person]]]:
        """
        Get all members of a family.
        
        Args:
            family_id: ID of family
            
        Returns:
            Dict with father, mother, and children
        """
        family = self.family_repo.find_by_id(family_id)

        if not family:
            return None

        father = None
        mother = None

        if family.father_id:
            father = self.person_repo.find_by_id(family.father_id)

        if family.mother_id:
            mother = self.person_repo.find_by_id(family.mother_id)

        return {
            "family": family,
            "father": father,
            "mother": mother,
            "children": [],  # Would load children
        }

    def create_family(
        self,
        father_id: Optional[int] = None,
        mother_id: Optional[int] = None,
    ) -> int:
        """
        Create a new family unit.
        
        Args:
            father_id: ID of father (optional)
            mother_id: ID of mother (optional)
            
        Returns:
            ID of created family
        """
        family = Family(father_id=father_id, mother_id=mother_id)

        family_id = self.family_repo.save(family)
        self.session.commit()
        return family_id

    def get_person_families(self, person_id: int) -> dict[str, List[Family]]:
        """
        Get all families a person belongs to.
        
        Args:
            person_id: ID of person
            
        Returns:
            Dict with 'as_parent' and 'as_child' families
        """
        as_parent = self.family_repo.find_by_parent(person_id)
        as_child_family = self.family_repo.find_by_child(person_id)

        return {
            "as_parent": as_parent,
            "as_child": [as_child_family] if as_child_family else [],
        }


class GenealogyService:
    """
    Service for advanced genealogical computations.
    
    Provides high-level access to genealogy algorithms.
    """

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.algorithms = GenealogyAlgorithms(session)
        self.relationship_detector = RelationshipDetector(session)
        self.sosa_calculator = SosaCalculator(session)

    def calculate_consanguinity(
        self, person_id: int, use_cache: bool = True
    ) -> float:
        """
        Calculate consanguinity coefficient for a person.
        
        Args:
            person_id: ID of person
            use_cache: Whether to use cached results
            
        Returns:
            Consanguinity coefficient (0.0 to 1.0)
        """
        return self.algorithms.calculate_consanguinity_advanced(
            person_id, use_cache=use_cache
        )

    def find_relationship(
        self, person1_id: int, person2_id: int
    ) -> Optional[RelationshipPath]:
        """
        Find relationship between two persons.
        
        Args:
            person1_id: ID of first person
            person2_id: ID of second person
            
        Returns:
            RelationshipPath object or None
        """
        return self.relationship_detector.find_shortest_path(
            person1_id, person2_id
        )

    def calculate_sosa_number(
        self, person_id: int, root_person_id: int
    ) -> Optional[int]:
        """
        Calculate Sosa number for a person relative to root.
        
        Args:
            person_id: ID of person to calculate Sosa for
            root_person_id: ID of root person (reference)
            
        Returns:
            Sosa number or None if not an ancestor
        """
        sosa_map = self.sosa_calculator.compute_sosa_numbers(root_person_id)
        return sosa_map.get(person_id)

    def get_ancestors(
        self, person_id: int, max_generations: int = 10
    ) -> List[Person]:
        """
        Get all ancestors up to max generations.
        
        Args:
            person_id: ID of person
            max_generations: Maximum generations to traverse
            
        Returns:
            List of ancestor Person objects
        """
        ancestor_ids = self.algorithms.get_all_ancestors(
            person_id, max_depth=max_generations
        )

        person_repo = get_person_repository(self.session)
        ancestors = []

        for ancestor_id in ancestor_ids:
            person = person_repo.find_by_id(ancestor_id)
            if person:
                ancestors.append(person)

        return ancestors

    def get_descendants(
        self, person_id: int, max_generations: int = 10
    ) -> List[Person]:
        """
        Get all descendants up to max generations.
        
        Args:
            person_id: ID of person
            max_generations: Maximum generations to traverse
            
        Returns:
            List of descendant Person objects
        """
        descendant_ids = self.algorithms.get_all_descendants(
            person_id, max_depth=max_generations
        )

        person_repo = get_person_repository(self.session)
        descendants = []

        for descendant_id in descendant_ids:
            person = person_repo.find_by_id(descendant_id)
            if person:
                descendants.append(person)

        return descendants


# Convenience factory functions
def get_person_service(session: Session) -> PersonService:
    """Create PersonService instance."""
    return PersonService(session)


def get_family_service(session: Session) -> FamilyService:
    """Create FamilyService instance."""
    return FamilyService(session)


def get_genealogy_service(session: Session) -> GenealogyService:
    """Create GenealogyService instance."""
    return GenealogyService(session)
