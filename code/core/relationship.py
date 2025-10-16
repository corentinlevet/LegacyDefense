"""
Advanced relationship detection engine for genealogical analysis.

This module provides sophisticated relationship detection capabilities,
including:
- Shortest path finding between any two persons
- Complex relationship naming (cousins, removed, half-siblings, etc.)
- Multiple relationship paths detection
- Relationship validation and simplification

Ported from OCaml implementation in geneweb/lib/relation.ml
"""

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from .database import DatabaseManager, FamilyORM, PersonORM


class FamilyLinkType(Enum):
    """Types of family links in a relationship path."""

    SELF = "self"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    HALF_SIBLING = "half_sibling"
    MATE = "mate"  # Spouse/partner


@dataclass
class RelationshipLink:
    """
    Represents a single link in a relationship path.
    
    Attributes:
        person_id: ID of the person at this step
        link_type: Type of relationship link
        family_id: Family through which this link goes (if applicable)
    """

    person_id: int
    link_type: FamilyLinkType
    family_id: Optional[int] = None

    def __repr__(self) -> str:
        return f"Link({self.person_id}, {self.link_type.value})"


@dataclass
class RelationshipPath:
    """
    Represents a complete path between two persons.
    
    Attributes:
        person1_id: Starting person ID
        person2_id: Ending person ID
        path: List of relationship links from person1 to person2
        distance: Total distance (number of links)
        description: Human-readable description
    """

    person1_id: int
    person2_id: int
    path: List[RelationshipLink]
    distance: int
    description: str

    def reverse(self) -> "RelationshipPath":
        """Return the reversed path (from person2 to person1)."""
        reversed_links = []
        for link in reversed(self.path):
            # Reverse the link type
            if link.link_type == FamilyLinkType.PARENT:
                reversed_type = FamilyLinkType.CHILD
            elif link.link_type == FamilyLinkType.CHILD:
                reversed_type = FamilyLinkType.PARENT
            else:
                reversed_type = link.link_type

            reversed_links.append(
                RelationshipLink(
                    person_id=link.person_id,
                    link_type=reversed_type,
                    family_id=link.family_id,
                )
            )

        return RelationshipPath(
            person1_id=self.person2_id,
            person2_id=self.person1_id,
            path=reversed_links,
            distance=self.distance,
            description=f"Inverse: {self.description}",
        )


class RelationshipDetector:
    """
    Detects and analyzes relationships between persons in a genealogy.
    
    Uses bidirectional breadth-first search (BFS) to find the shortest
    path between any two persons, considering all types of family links.
    """

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the relationship detector."""
        self.db_manager = db_manager

    def find_shortest_path(
        self,
        session,
        person1_id: int,
        person2_id: int,
        excluded_families: Optional[Set[int]] = None,
    ) -> Optional[RelationshipPath]:
        """
        Find the shortest relationship path between two persons.
        
        Uses bidirectional BFS to efficiently find the shortest path,
        exploring from both persons simultaneously until they meet.
        
        Args:
            session: SQLAlchemy session
            person1_id: First person ID
            person2_id: Second person ID
            excluded_families: Set of family IDs to exclude from search
            
        Returns:
            RelationshipPath if found, None otherwise
        """
        if person1_id == person2_id:
            return RelationshipPath(
                person1_id=person1_id,
                person2_id=person2_id,
                path=[
                    RelationshipLink(
                        person_id=person1_id, link_type=FamilyLinkType.SELF
                    )
                ],
                distance=0,
                description="Même personne",
            )

        if excluded_families is None:
            excluded_families = set()

        # Mark visited persons and their incoming link
        # Dict[person_id] = (from_direction, previous_person_id, link_type, family_id)
        visited_from_p1: Dict[int, Tuple[int, FamilyLinkType, Optional[int]]] = {}
        visited_from_p2: Dict[int, Tuple[int, FamilyLinkType, Optional[int]]] = {}

        # Queues for BFS
        queue_p1 = deque([(person1_id, None, FamilyLinkType.SELF, None)])
        queue_p2 = deque([(person2_id, None, FamilyLinkType.SELF, None)])

        visited_from_p1[person1_id] = (person1_id, FamilyLinkType.SELF, None)
        visited_from_p2[person2_id] = (person2_id, FamilyLinkType.SELF, None)

        processed_families = set()

        def get_neighbors(person_id: int) -> List[Tuple[int, FamilyLinkType, int]]:
            """Get all neighboring persons and their link types."""
            neighbors = []
            person = (
                session.query(PersonORM).filter(PersonORM.id == person_id).first()
            )

            if not person:
                return neighbors

            # Parents (through parent family)
            if person.parent_family and person.parent_family.id not in excluded_families:
                family_id = person.parent_family.id
                if family_id not in processed_families:
                    processed_families.add(family_id)

                    if person.parent_family.father_id:
                        neighbors.append(
                            (
                                person.parent_family.father_id,
                                FamilyLinkType.PARENT,
                                family_id,
                            )
                        )
                    if person.parent_family.mother_id:
                        neighbors.append(
                            (
                                person.parent_family.mother_id,
                                FamilyLinkType.PARENT,
                                family_id,
                            )
                        )

                    # Siblings (through same parent family)
                    siblings = (
                        session.query(PersonORM)
                        .filter(
                            PersonORM.parent_family_id == family_id,
                            PersonORM.id != person_id,
                        )
                        .all()
                    )

                    for sibling in siblings:
                        neighbors.append(
                            (sibling.id, FamilyLinkType.SIBLING, family_id)
                        )

            # Spouses and children (through families where person is parent)
            families = (
                session.query(FamilyORM)
                .filter(
                    (FamilyORM.father_id == person_id)
                    | (FamilyORM.mother_id == person_id)
                )
                .all()
            )

            for family in families:
                if family.id in excluded_families:
                    continue

                if family.id not in processed_families:
                    processed_families.add(family.id)

                    # Spouse/mate
                    if family.father_id == person_id and family.mother_id:
                        neighbors.append(
                            (family.mother_id, FamilyLinkType.MATE, family.id)
                        )
                    elif family.mother_id == person_id and family.father_id:
                        neighbors.append(
                            (family.father_id, FamilyLinkType.MATE, family.id)
                        )

                    # Children
                    children = (
                        session.query(PersonORM)
                        .filter(PersonORM.parent_family_id == family.id)
                        .all()
                    )

                    for child in children:
                        neighbors.append((child.id, FamilyLinkType.CHILD, family.id))

            return neighbors

        # Bidirectional BFS
        while queue_p1 or queue_p2:
            # Alternate between expanding from p1 and p2
            # Process smaller queue first for efficiency
            if len(queue_p1) <= len(queue_p2) and queue_p1:
                current_id, prev_id, link_type, family_id = queue_p1.popleft()

                # Check if we've met someone from the other direction
                if current_id in visited_from_p2:
                    # Found a path! Reconstruct it
                    return self._reconstruct_path(
                        person1_id,
                        person2_id,
                        current_id,
                        visited_from_p1,
                        visited_from_p2,
                    )

                # Expand neighbors
                for neighbor_id, neighbor_link, neighbor_family in get_neighbors(
                    current_id
                ):
                    if neighbor_id not in visited_from_p1:
                        visited_from_p1[neighbor_id] = (
                            current_id,
                            neighbor_link,
                            neighbor_family,
                        )
                        queue_p1.append(
                            (neighbor_id, current_id, neighbor_link, neighbor_family)
                        )

            elif queue_p2:
                current_id, prev_id, link_type, family_id = queue_p2.popleft()

                # Check if we've met someone from the other direction
                if current_id in visited_from_p1:
                    # Found a path! Reconstruct it
                    return self._reconstruct_path(
                        person1_id,
                        person2_id,
                        current_id,
                        visited_from_p1,
                        visited_from_p2,
                    )

                # Expand neighbors
                for neighbor_id, neighbor_link, neighbor_family in get_neighbors(
                    current_id
                ):
                    if neighbor_id not in visited_from_p2:
                        visited_from_p2[neighbor_id] = (
                            current_id,
                            neighbor_link,
                            neighbor_family,
                        )
                        queue_p2.append(
                            (neighbor_id, current_id, neighbor_link, neighbor_family)
                        )

        # No path found
        return None

    def _reconstruct_path(
        self,
        person1_id: int,
        person2_id: int,
        meeting_point: int,
        visited_from_p1: Dict[int, Tuple[int, FamilyLinkType, Optional[int]]],
        visited_from_p2: Dict[int, Tuple[int, FamilyLinkType, Optional[int]]],
    ) -> RelationshipPath:
        """Reconstruct the path from the bidirectional search results."""
        # Build path from person1 to meeting point
        path_p1 = []
        current = meeting_point

        while current != person1_id:
            prev, link_type, family_id = visited_from_p1[current]
            path_p1.insert(
                0,
                RelationshipLink(
                    person_id=current, link_type=link_type, family_id=family_id
                ),
            )
            current = prev

        # Build path from meeting point to person2
        path_p2 = []
        current = meeting_point

        while current != person2_id:
            prev, link_type, family_id = visited_from_p2[current]
            # Reverse link types for path from p1 to p2
            reversed_link = self._reverse_link_type(link_type)
            path_p2.append(
                RelationshipLink(
                    person_id=prev, link_type=reversed_link, family_id=family_id
                )
            )
            current = prev

        # Combine paths
        full_path = (
            [
                RelationshipLink(
                    person_id=person1_id, link_type=FamilyLinkType.SELF
                )
            ]
            + path_p1
            + path_p2
        )

        # Generate description
        description = self._generate_relationship_description(full_path)

        return RelationshipPath(
            person1_id=person1_id,
            person2_id=person2_id,
            path=full_path,
            distance=len(full_path) - 1,
            description=description,
        )

    def _reverse_link_type(self, link_type: FamilyLinkType) -> FamilyLinkType:
        """Reverse a link type for bidirectional path reconstruction."""
        if link_type == FamilyLinkType.PARENT:
            return FamilyLinkType.CHILD
        elif link_type == FamilyLinkType.CHILD:
            return FamilyLinkType.PARENT
        else:
            return link_type

    def _generate_relationship_description(
        self, path: List[RelationshipLink]
    ) -> str:
        """
        Generate a human-readable relationship description from a path.
        
        Args:
            path: List of relationship links
            
        Returns:
            Human-readable description (in French)
        """
        if len(path) <= 1:
            return "Même personne"

        # Count specific link types
        parents = sum(1 for link in path if link.link_type == FamilyLinkType.PARENT)
        children = sum(1 for link in path if link.link_type == FamilyLinkType.CHILD)
        siblings = sum(1 for link in path if link.link_type == FamilyLinkType.SIBLING)
        half_siblings = sum(
            1 for link in path if link.link_type == FamilyLinkType.HALF_SIBLING
        )
        mates = sum(1 for link in path if link.link_type == FamilyLinkType.MATE)

        # Direct parent/child
        if len(path) == 2 and path[1].link_type == FamilyLinkType.PARENT:
            return "Parent direct"
        if len(path) == 2 and path[1].link_type == FamilyLinkType.CHILD:
            return "Enfant direct"

        # Siblings
        if len(path) == 2 and path[1].link_type == FamilyLinkType.SIBLING:
            return "Frères/Sœurs"
        if len(path) == 2 and path[1].link_type == FamilyLinkType.HALF_SIBLING:
            return "Demi-frères/Demi-sœurs"

        # Spouse/mate
        if len(path) == 2 and path[1].link_type == FamilyLinkType.MATE:
            return "Conjoint(e)"

        # Grandparents/grandchildren
        if parents == 2 and children == 0:
            return "Grand-parent"
        if children == 2 and parents == 0:
            return "Petit-enfant"
        if parents == 3 and children == 0:
            return "Arrière-grand-parent"
        if children == 3 and parents == 0:
            return "Arrière-petit-enfant"

        # Uncle/aunt, nephew/niece
        if parents == 1 and siblings == 1 and len(path) == 3:
            return "Oncle/Tante"
        if children == 1 and siblings == 1 and len(path) == 3:
            return "Neveu/Nièce"

        # Cousins
        if parents == 2 and siblings == 1 and children == 0:
            # Going up 2 generations through siblings = cousins
            # But this would be from child's perspective
            return "Cousin(e) germain(e)"

        # Simplified path description
        up_count = parents
        down_count = children
        lateral_count = siblings + half_siblings

        if up_count > 0 and down_count > 0:
            if lateral_count > 0:
                cousin_degree = min(up_count, down_count)
                removed = abs(up_count - down_count)
                if removed == 0:
                    return f"Cousin(e) au {cousin_degree}e degré"
                else:
                    return f"Cousin(e) au {cousin_degree}e degré, {removed} fois enlevé"
            else:
                return f"Relation: {up_count}↑ {down_count}↓"
        elif up_count > 0:
            if up_count == 1:
                return "Parent"
            elif up_count == 2:
                return "Grand-parent"
            else:
                return f"Ancêtre ({up_count} générations)"
        elif down_count > 0:
            if down_count == 1:
                return "Enfant"
            elif down_count == 2:
                return "Petit-enfant"
            else:
                return f"Descendant ({down_count} générations)"
        else:
            return f"Relation complexe (distance: {len(path) - 1})"

    def find_all_paths(
        self,
        session,
        person1_id: int,
        person2_id: int,
        max_paths: int = 10,
        max_distance: int = 10,
    ) -> List[RelationshipPath]:
        """
        Find multiple relationship paths between two persons.
        
        Args:
            session: SQLAlchemy session
            person1_id: First person ID
            person2_id: Second person ID
            max_paths: Maximum number of paths to find
            max_distance: Maximum path distance to explore
            
        Returns:
            List of relationship paths, sorted by distance
        """
        # NOTE: This is a simplified implementation
        # A full implementation would use K-shortest paths algorithm

        paths = []

        # Find the shortest path first
        shortest = self.find_shortest_path(session, person1_id, person2_id)
        if shortest:
            paths.append(shortest)

        # Try to find alternative paths by excluding families in the shortest path
        if shortest and len(paths) < max_paths:
            excluded_families = {
                link.family_id for link in shortest.path if link.family_id
            }

            # Try excluding each family one at a time to find alternatives
            for family_id in excluded_families:
                if len(paths) >= max_paths:
                    break

                alt_path = self.find_shortest_path(
                    session, person1_id, person2_id, {family_id}
                )

                if alt_path and alt_path.distance <= max_distance:
                    # Check if this is a genuinely different path
                    if not any(
                        self._paths_are_similar(alt_path, existing)
                        for existing in paths
                    ):
                        paths.append(alt_path)

        return sorted(paths, key=lambda p: p.distance)

    def _paths_are_similar(
        self, path1: RelationshipPath, path2: RelationshipPath
    ) -> bool:
        """Check if two paths are essentially the same."""
        if path1.distance != path2.distance:
            return False

        # Compare person IDs in paths
        ids1 = {link.person_id for link in path1.path}
        ids2 = {link.person_id for link in path2.path}

        # If they share most persons, they're similar
        overlap = len(ids1 & ids2)
        return overlap > len(ids1) * 0.8  # 80% overlap threshold

    def analyze_relationship(
        self, session, person1_id: int, person2_id: int
    ) -> Dict:
        """
        Provide a comprehensive analysis of the relationship between two persons.
        
        Args:
            session: SQLAlchemy session
            person1_id: First person ID
            person2_id: Second person ID
            
        Returns:
            Dictionary with relationship analysis
        """
        analysis = {
            "person1_id": person1_id,
            "person2_id": person2_id,
            "shortest_path": None,
            "alternative_paths": [],
            "common_ancestors": [],
            "relationship_type": "unknown",
            "description": "",
        }

        # Find shortest path
        shortest = self.find_shortest_path(session, person1_id, person2_id)
        if shortest:
            analysis["shortest_path"] = shortest
            analysis["relationship_type"] = self._classify_relationship_type(shortest)
            analysis["description"] = shortest.description

            # Find alternative paths
            all_paths = self.find_all_paths(session, person1_id, person2_id)
            analysis["alternative_paths"] = all_paths[1:]  # Exclude shortest

        return analysis

    def _classify_relationship_type(self, path: RelationshipPath) -> str:
        """Classify the relationship type based on path."""
        if path.distance == 0:
            return "self"
        elif path.distance == 1:
            link_type = path.path[1].link_type
            if link_type == FamilyLinkType.PARENT:
                return "parent_child"
            elif link_type == FamilyLinkType.CHILD:
                return "child_parent"
            elif link_type == FamilyLinkType.SIBLING:
                return "sibling"
            elif link_type == FamilyLinkType.MATE:
                return "spouse"
        elif path.distance == 2:
            return "close_relative"
        else:
            return "distant_relative"


# Convenience function
def find_relationship(
    session, db_manager: DatabaseManager, person1_id: int, person2_id: int
) -> Optional[RelationshipPath]:
    """
    Convenience function to find relationship between two persons.
    
    Args:
        session: SQLAlchemy session
        db_manager: Database manager
        person1_id: First person ID
        person2_id: Second person ID
        
    Returns:
        RelationshipPath if found, None otherwise
    """
    detector = RelationshipDetector(db_manager)
    return detector.find_shortest_path(session, person1_id, person2_id)
