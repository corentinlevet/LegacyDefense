"""
Sosa-Stradonitz numbering system for genealogical trees.

This module implements the Sosa-Stradonitz numbering system, also known as
the Ahnentafel system, which assigns a unique number to each ancestor of
a person based on their position in the genealogical tree.

The system works as follows:
- The subject (root person) is numbered 1
- The father of person n is 2n
- The mother of person n is 2n + 1
- Therefore, any person n has:
  - Father: 2n
  - Mother: 2n + 1
  - Children: n // 2

This creates a binary tree structure where:
- Even numbers are males (fathers)
- Odd numbers (except 1) are females (mothers)
- Generation g contains persons numbered from 2^g to 2^(g+1) - 1

Ported from OCaml implementation in geneweb/lib/sosa/geneweb_sosa.zarith.ml
"""

from typing import Dict, List, Optional, Set, Tuple


class Sosa:
    """
    Represents a Sosa number (arbitrary precision integer for large genealogies).
    
    Uses Python's built-in arbitrary precision integers for genealogies
    spanning many generations.
    
    Attributes:
        value (int): The Sosa number value (must be non-negative)
    """

    def __init__(self, value: int):
        """
        Initialize a Sosa number.
        
        Args:
            value: The Sosa number (must be >= 0)
            
        Raises:
            ValueError: If value is negative
        """
        if value < 0:
            raise ValueError("Sosa number must be non-negative")
        self._value = value

    @classmethod
    def of_int(cls, i: int) -> "Sosa":
        """Create a Sosa from an integer."""
        return cls(i)

    @classmethod
    def zero(cls) -> "Sosa":
        """Return Sosa number 0."""
        return cls(0)

    @classmethod
    def one(cls) -> "Sosa":
        """Return Sosa number 1 (the root person)."""
        return cls(1)

    @classmethod
    def two(cls) -> "Sosa":
        """Return Sosa number 2."""
        return cls(2)

    @property
    def value(self) -> int:
        """Get the integer value of the Sosa number."""
        return self._value

    def __eq__(self, other) -> bool:
        """Check equality with another Sosa or int."""
        if isinstance(other, Sosa):
            return self._value == other._value
        elif isinstance(other, int):
            return self._value == other
        return False

    def __lt__(self, other) -> bool:
        """Less than comparison."""
        if isinstance(other, Sosa):
            return self._value < other._value
        elif isinstance(other, int):
            return self._value < other
        return NotImplemented

    def __gt__(self, other) -> bool:
        """Greater than comparison."""
        if isinstance(other, Sosa):
            return self._value > other._value
        elif isinstance(other, int):
            return self._value > other
        return NotImplemented

    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return self == other or self < other

    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return self == other or self > other

    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self._value)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Sosa({self._value})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return str(self._value)

    def half(self) -> "Sosa":
        """
        Return half of this Sosa number (parent of a child).
        
        Returns:
            Sosa number divided by 2
        """
        return Sosa(self._value // 2)

    def twice(self) -> "Sosa":
        """
        Return twice this Sosa number.
        
        Returns:
            Sosa number multiplied by 2
        """
        return Sosa(self._value * 2)

    def father(self) -> "Sosa":
        """
        Get the Sosa number of the father (2n).
        
        Returns:
            Sosa number of the father
        """
        return Sosa(self._value * 2)

    def mother(self) -> "Sosa":
        """
        Get the Sosa number of the mother (2n + 1).
        
        Returns:
            Sosa number of the mother
        """
        return Sosa(self._value * 2 + 1)

    def parent(self) -> "Sosa":
        """
        Get the parent Sosa number (child -> parent).
        
        Returns:
            Sosa number of the parent (n // 2)
        """
        return self.half()

    def is_father(self) -> bool:
        """
        Check if this Sosa number represents a father (even number > 0).
        
        Returns:
            True if even and positive, False otherwise
        """
        return self._value > 0 and self._value % 2 == 0

    def is_mother(self) -> bool:
        """
        Check if this Sosa number represents a mother (odd number > 1).
        
        Returns:
            True if odd and > 1, False otherwise
        """
        return self._value > 1 and self._value % 2 == 1

    def is_even(self) -> bool:
        """Check if the Sosa number is even."""
        return self._value % 2 == 0

    def is_odd(self) -> bool:
        """Check if the Sosa number is odd."""
        return self._value % 2 == 1

    def generation(self) -> int:
        """
        Get the generation number (0-indexed from the root).
        
        The generation is determined by: gen = floor(log2(n))
        - Generation 0: person 1 (root)
        - Generation 1: persons 2-3 (parents)
        - Generation 2: persons 4-7 (grandparents)
        - Generation g: persons 2^g to 2^(g+1) - 1
        
        Returns:
            Generation number (0 for root, 1 for parents, etc.)
        """
        if self._value == 0:
            return 0
        return self._value.bit_length() - 1

    def add(self, other: "Sosa") -> "Sosa":
        """Add two Sosa numbers."""
        return Sosa(self._value + other._value)

    def sub(self, other: "Sosa") -> "Sosa":
        """Subtract two Sosa numbers."""
        return Sosa(max(0, self._value - other._value))

    def increment(self, inc: int) -> "Sosa":
        """
        Increment Sosa number by an integer value.
        
        Args:
            inc: Integer increment
            
        Returns:
            New Sosa number incremented by inc
        """
        return Sosa(self._value + inc)

    def to_string_sep(self, sep: str = " ") -> str:
        """
        Convert to string with separator every 3 digits.
        
        Args:
            sep: Separator to use (default: space)
            
        Returns:
            Formatted string (e.g., "1 234 567")
        """
        s = str(self._value)
        if len(s) <= 3:
            return s

        # Insert separator every 3 digits from right to left
        parts = []
        for i in range(len(s), 0, -3):
            parts.insert(0, s[max(0, i - 3) : i])

        return sep.join(parts)

    def branches(self) -> List[int]:
        """
        Get the branch path from root to this ancestor.
        
        Returns a list of 0s and 1s representing the path:
        - 0 means "go to father"
        - 1 means "go to mother"
        
        For example, Sosa 5 = binary 101:
        - From person 1, go to mother (1) -> person 3
        - From person 3, go to father (0) -> person 6... wait, that's wrong
        
        Actually, reading the binary representation from left to right
        (after removing the leading 1) gives the path:
        - Sosa 5 = 101 in binary
        - Path = [0, 1] = father, then mother
        - 1 -> 2 (father) -> 5 (mother of 2)
        
        Returns:
            List of 0 (father) and 1 (mother) indicating the path
        """
        if self._value <= 1:
            return []

        # Get binary representation without '0b' prefix
        binary = bin(self._value)[2:]

        # Remove the leading '1' (represents the root)
        path_binary = binary[1:]

        # Convert to list of integers
        return [int(bit) for bit in path_binary]

    def __int__(self) -> int:
        """Convert to int."""
        return self._value


class SosaCalculator:
    """
    Calculator for Sosa numbers in a genealogical database.
    
    This class provides utilities to assign and retrieve Sosa numbers
    for persons in a genealogical tree, with caching for performance.
    """

    def __init__(self):
        """Initialize the Sosa calculator with empty cache."""
        self._cache: Dict[int, Sosa] = {}  # person_id -> Sosa number
        self._reverse_cache: Dict[Sosa, int] = {}  # Sosa -> person_id

    def clear_cache(self):
        """Clear the Sosa number cache."""
        self._cache.clear()
        self._reverse_cache.clear()

    def get_sosa(self, person_id: int) -> Optional[Sosa]:
        """
        Get the Sosa number for a person.
        
        Args:
            person_id: Database ID of the person
            
        Returns:
            Sosa number if assigned, None otherwise
        """
        return self._cache.get(person_id)

    def get_person_id(self, sosa: Sosa) -> Optional[int]:
        """
        Get the person ID for a given Sosa number.
        
        Args:
            sosa: Sosa number
            
        Returns:
            Person ID if found, None otherwise
        """
        return self._reverse_cache.get(sosa)

    def set_sosa(self, person_id: int, sosa: Sosa):
        """
        Assign a Sosa number to a person.
        
        Args:
            person_id: Database ID of the person
            sosa: Sosa number to assign
        """
        self._cache[person_id] = sosa
        self._reverse_cache[sosa] = person_id

    def compute_sosa_tree(self, session, root_person_id: int) -> Dict[int, Sosa]:
        """
        Compute Sosa numbers for all ancestors of a root person.
        
        This method traverses the genealogical tree starting from the root
        person (assigned Sosa 1) and assigns Sosa numbers to all ancestors:
        - Father gets 2n
        - Mother gets 2n + 1
        
        Args:
            session: SQLAlchemy session
            root_person_id: Database ID of the root person (will be Sosa 1)
            
        Returns:
            Dictionary mapping person_id to Sosa number
        """
        from .database import PersonORM

        # Clear existing cache
        self.clear_cache()

        # Assign Sosa 1 to root
        self.set_sosa(root_person_id, Sosa.one())

        # BFS to assign Sosa numbers to ancestors
        queue = [(root_person_id, Sosa.one())]
        visited = set()

        while queue:
            current_id, current_sosa = queue.pop(0)

            if current_id in visited:
                continue
            visited.add(current_id)

            # Get person from database
            person = (
                session.query(PersonORM).filter(PersonORM.id == current_id).first()
            )

            if not person or not person.parent_family:
                continue

            family = person.parent_family

            # Assign Sosa to father (2n)
            if family.father_id:
                father_sosa = current_sosa.father()
                self.set_sosa(family.father_id, father_sosa)
                queue.append((family.father_id, father_sosa))

            # Assign Sosa to mother (2n + 1)
            if family.mother_id:
                mother_sosa = current_sosa.mother()
                self.set_sosa(family.mother_id, mother_sosa)
                queue.append((family.mother_id, mother_sosa))

        return dict(self._cache)

    def get_ancestors_by_generation(
        self, session, root_person_id: int, max_generation: int = 10
    ) -> Dict[int, List[Tuple[int, Sosa]]]:
        """
        Get ancestors organized by generation.
        
        Args:
            session: SQLAlchemy session
            root_person_id: Root person ID
            max_generation: Maximum generation to compute (default: 10)
            
        Returns:
            Dict mapping generation number to list of (person_id, Sosa) tuples
        """
        # Compute Sosa tree
        sosa_map = self.compute_sosa_tree(session, root_person_id)

        # Organize by generation
        by_generation: Dict[int, List[Tuple[int, Sosa]]] = {}

        for person_id, sosa in sosa_map.items():
            gen = sosa.generation()
            if gen > max_generation:
                continue

            if gen not in by_generation:
                by_generation[gen] = []

            by_generation[gen].append((person_id, sosa))

        # Sort each generation by Sosa number
        for gen in by_generation:
            by_generation[gen].sort(key=lambda x: x[1].value)

        return by_generation

    def get_generation_range(self, generation: int) -> Tuple[Sosa, Sosa]:
        """
        Get the range of Sosa numbers for a given generation.
        
        Args:
            generation: Generation number (0 = root, 1 = parents, etc.)
            
        Returns:
            Tuple of (min_sosa, max_sosa) for the generation
        """
        min_sosa = Sosa(2**generation)
        max_sosa = Sosa(2 ** (generation + 1) - 1)
        return (min_sosa, max_sosa)

    def get_all_in_generation(self, generation: int) -> Set[Sosa]:
        """
        Get all possible Sosa numbers in a generation.
        
        Args:
            generation: Generation number
            
        Returns:
            Set of all Sosa numbers in that generation
        """
        min_val = 2**generation
        max_val = 2 ** (generation + 1)
        return {Sosa(i) for i in range(min_val, max_val)}

    def find_common_ancestor_sosa(
        self, person1_sosa: Sosa, person2_sosa: Sosa
    ) -> Optional[Sosa]:
        """
        Find the most recent common ancestor (MRCA) by Sosa numbers.
        
        This uses the property that the MRCA is found by following
        the parent path until both persons meet.
        
        Args:
            person1_sosa: Sosa number of first person
            person2_sosa: Sosa number of second person
            
        Returns:
            Sosa number of MRCA, or None if no common ancestor
        """
        # Make copies to avoid modifying originals
        s1 = Sosa(person1_sosa.value)
        s2 = Sosa(person2_sosa.value)

        # Bring both to the same generation first
        while s1.generation() > s2.generation():
            s1 = s1.parent()

        while s2.generation() > s1.generation():
            s2 = s2.parent()

        # Now traverse upward together until they meet
        while s1 != s2 and s1.value > 0 and s2.value > 0:
            s1 = s1.parent()
            s2 = s2.parent()

        if s1 == s2 and s1.value > 0:
            return s1

        return None

    def get_relationship_from_sosa(
        self, person1_sosa: Sosa, person2_sosa: Sosa
    ) -> str:
        """
        Determine relationship between two persons from their Sosa numbers.
        
        Args:
            person1_sosa: Sosa number of first person
            person2_sosa: Sosa number of second person
            
        Returns:
            Human-readable relationship description
        """
        if person1_sosa == person2_sosa:
            return "Même personne"

        # Check for direct parent-child relationship
        if person1_sosa.parent() == person2_sosa:
            if person1_sosa.is_even():
                return "Fils/Fille (père)"
            else:
                return "Fils/Fille (mère)"

        if person2_sosa.parent() == person1_sosa:
            if person2_sosa.is_even():
                return "Père (fils)"
            else:
                return "Mère (fille)"

        # Check for siblings (same parent)
        if person1_sosa.parent() == person2_sosa.parent():
            return "Frères/Sœurs"

        # Find common ancestor
        mrca = self.find_common_ancestor_sosa(person1_sosa, person2_sosa)

        if mrca is None:
            return "Non apparentés (dans cette lignée)"

        # Calculate distances
        dist1 = person1_sosa.generation() - mrca.generation()
        dist2 = person2_sosa.generation() - mrca.generation()

        if dist1 == 1 and dist2 == 1:
            return "Frères/Sœurs"
        elif dist1 == 2 and dist2 == 2:
            return "Cousins germains"
        elif dist1 == 1 and dist2 == 2:
            return "Oncle/Tante - Neveu/Nièce"
        elif dist1 == 2 and dist2 == 1:
            return "Neveu/Nièce - Oncle/Tante"
        else:
            cousin_degree = min(dist1, dist2) - 1
            removed = abs(dist1 - dist2)
            if removed == 0:
                return f"Cousins au {cousin_degree}e degré"
            else:
                return f"Cousins au {cousin_degree}e degré, {removed} fois enlevés"

    def format_sosa_tree(
        self, session, root_person_id: int, max_generation: int = 5
    ) -> str:
        """
        Format a Sosa tree as a human-readable string.
        
        Args:
            session: SQLAlchemy session
            root_person_id: Root person ID
            max_generation: Maximum generation to display
            
        Returns:
            Formatted string representation of the tree
        """
        from .database import PersonORM

        by_gen = self.get_ancestors_by_generation(
            session, root_person_id, max_generation
        )

        lines = []
        lines.append("=== SOSA TREE ===\n")

        for gen in sorted(by_gen.keys()):
            lines.append(f"\nGénération {gen}:")
            min_s, max_s = self.get_generation_range(gen)
            lines.append(f"  (Sosa {min_s} à {max_s})")

            for person_id, sosa in by_gen[gen]:
                person = (
                    session.query(PersonORM).filter(PersonORM.id == person_id).first()
                )
                if person:
                    name = f"{person.first_name} {person.surname}"
                    sex_value = getattr(person.sex, "value", person.sex)
                    lines.append(
                        f"  [{sosa.to_string_sep()}] {sex_indicator} {name}"
                    )

        return "\n".join(lines)


# Convenience functions
def sosa_of_int(i: int) -> Sosa:
    """Create a Sosa number from an integer."""
    return Sosa.of_int(i)


def sosa_zero() -> Sosa:
    """Return Sosa 0."""
    return Sosa.zero()


def sosa_one() -> Sosa:
    """Return Sosa 1 (root person)."""
    return Sosa.one()


def sosa_two() -> Sosa:
    """Return Sosa 2."""
    return Sosa.two()
