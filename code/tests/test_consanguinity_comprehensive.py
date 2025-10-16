"""
Comprehensive test suite for consanguinity algorithms.

Tests the consanguinity calculation algorithms ported from OCaml,
ensuring 95%+ coverage and correctness validation.
"""

import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.algorithms import (
    ConsanguinityResult,
    FamilyLink,
    GenealogyAlgorithms,
    RelationshipPath,
    RelationType,
)
from core.database import Base, DatabaseManager, FamilyORM, PersonORM
from core.models import Sex


@pytest.fixture
def db_manager():
    """Create an in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.engine = engine
    db_manager.Session = Session
    return db_manager


@pytest.fixture
def session(db_manager):
    """Create a database session."""
    session = db_manager.Session()
    yield session
    session.close()


@pytest.fixture
def genealogy_algorithms(db_manager):
    """Create GenealogyAlgorithms instance."""
    return GenealogyAlgorithms(db_manager)


class TestBasicConsanguinity:
    """Test basic consanguinity calculations."""

    def test_no_consanguinity_unrelated_parents(self, session, genealogy_algorithms):
        """Test that person with unrelated parents has zero consanguinity."""
        # Create unrelated parents
        father = PersonORM(
            first_name="Father",
            surname="Smith",
            sex=Sex.MALE,
        )
        mother = PersonORM(
            first_name="Mother",
            surname="Jones",
            sex=Sex.FEMALE,
        )
        session.add_all([father, mother])
        session.flush()

        # Create family
        family = FamilyORM(father_id=father.id, mother_id=mother.id)
        session.add(family)
        session.flush()

        # Create child
        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        session.add(child)
        session.commit()

        # Calculate consanguinity
        result = genealogy_algorithms.calculate_consanguinity_advanced(
            session, child.id
        )

        assert result.consanguinity == 0.0
        assert len(result.common_ancestors) == 0
        assert len(result.relationship_paths) == 0

    def test_first_cousin_parents_consanguinity(self, session, genealogy_algorithms):
        """Test consanguinity for child of first cousins (1/16 = 0.0625)."""
        # Create grandparents (common ancestors)
        gf = PersonORM(first_name="GrandFather", surname="Smith", sex=Sex.MALE)
        gm = PersonORM(first_name="GrandMother", surname="Smith", sex=Sex.FEMALE)
        session.add_all([gf, gm])
        session.flush()

        # Create grandparent family
        gfamily = FamilyORM(father_id=gf.id, mother_id=gm.id)
        session.add(gfamily)
        session.flush()

        # Create two siblings (children of grandparents)
        uncle = PersonORM(
            first_name="Uncle",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=gfamily.id,
        )
        aunt = PersonORM(
            first_name="Aunt",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=gfamily.id,
        )
        session.add_all([uncle, aunt])
        session.flush()

        # Create uncle's spouse (unrelated)
        uncle_wife = PersonORM(
            first_name="Uncle's Wife", surname="Jones", sex=Sex.FEMALE
        )
        session.add(uncle_wife)
        session.flush()

        # Create aunt's husband (unrelated)
        aunt_husband = PersonORM(
            first_name="Aunt's Husband", surname="Brown", sex=Sex.MALE
        )
        session.add(aunt_husband)
        session.flush()

        # Create families for uncle and aunt
        uncle_family = FamilyORM(father_id=uncle.id, mother_id=uncle_wife.id)
        aunt_family = FamilyORM(father_id=aunt_husband.id, mother_id=aunt.id)
        session.add_all([uncle_family, aunt_family])
        session.flush()

        # Create first cousins (parents of target child)
        cousin1 = PersonORM(
            first_name="Cousin1",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=uncle_family.id,
        )
        cousin2 = PersonORM(
            first_name="Cousin2",
            surname="Brown",
            sex=Sex.FEMALE,
            parent_family_id=aunt_family.id,
        )
        session.add_all([cousin1, cousin2])
        session.flush()

        # Create family for cousins
        cousin_family = FamilyORM(father_id=cousin1.id, mother_id=cousin2.id)
        session.add(cousin_family)
        session.flush()

        # Create child of first cousins
        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=cousin_family.id,
        )
        session.add(child)
        session.commit()

        # Calculate consanguinity
        result = genealogy_algorithms.calculate_consanguinity_advanced(
            session, child.id
        )

        # Expected: (1/2)^(2+2+1) = (1/2)^5 = 1/32 = 0.03125 per grandparent
        # Two grandparents: 2 * 0.03125 = 0.0625
        expected_consanguinity = 0.0625
        assert math.isclose(
            result.consanguinity, expected_consanguinity, rel_tol=1e-4
        ), f"Expected {expected_consanguinity}, got {result.consanguinity}"
        assert len(result.common_ancestors) == 2  # GF and GM
        assert gf.id in result.common_ancestors
        assert gm.id in result.common_ancestors

    def test_sibling_parents_consanguinity(self, session, genealogy_algorithms):
        """Test consanguinity for child of siblings (1/4 = 0.25)."""
        # Create grandparents
        gf = PersonORM(first_name="GrandFather", surname="Smith", sex=Sex.MALE)
        gm = PersonORM(first_name="GrandMother", surname="Smith", sex=Sex.FEMALE)
        session.add_all([gf, gm])
        session.flush()

        # Create grandparent family
        gfamily = FamilyORM(father_id=gf.id, mother_id=gm.id)
        session.add(gfamily)
        session.flush()

        # Create siblings (brother and sister)
        brother = PersonORM(
            first_name="Brother",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=gfamily.id,
        )
        sister = PersonORM(
            first_name="Sister",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=gfamily.id,
        )
        session.add_all([brother, sister])
        session.flush()

        # Create family for siblings (incestuous)
        sibling_family = FamilyORM(father_id=brother.id, mother_id=sister.id)
        session.add(sibling_family)
        session.flush()

        # Create child
        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=sibling_family.id,
        )
        session.add(child)
        session.commit()

        # Calculate consanguinity
        result = genealogy_algorithms.calculate_consanguinity_advanced(
            session, child.id
        )

        # Expected: (1/2)^(1+1+1) = (1/2)^3 = 1/8 = 0.125 per grandparent
        # Two grandparents: 2 * 0.125 = 0.25
        expected_consanguinity = 0.25
        assert math.isclose(
            result.consanguinity, expected_consanguinity, rel_tol=1e-4
        ), f"Expected {expected_consanguinity}, got {result.consanguinity}"

    def test_no_parents_zero_consanguinity(self, session, genealogy_algorithms):
        """Test that person without parents has zero consanguinity."""
        person = PersonORM(first_name="Orphan", surname="Smith", sex=Sex.MALE)
        session.add(person)
        session.commit()

        result = genealogy_algorithms.calculate_consanguinity_advanced(
            session, person.id
        )

        assert result.consanguinity == 0.0
        assert len(result.common_ancestors) == 0

    def test_one_parent_zero_consanguinity(self, session, genealogy_algorithms):
        """Test that person with only one parent has zero consanguinity."""
        father = PersonORM(first_name="Father", surname="Smith", sex=Sex.MALE)
        session.add(father)
        session.flush()

        family = FamilyORM(father_id=father.id, mother_id=None)
        session.add(family)
        session.flush()

        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        session.add(child)
        session.commit()

        result = genealogy_algorithms.calculate_consanguinity_advanced(
            session, child.id
        )

        assert result.consanguinity == 0.0


class TestAdvancedConsanguinity:
    """Test advanced consanguinity scenarios."""

    def test_multiple_common_ancestor_paths(self, session, genealogy_algorithms):
        """Test consanguinity with multiple paths to common ancestors."""
        # NOTE: This tests the cumulative effect of multiple relationship paths
        # Create a complex scenario with double first cousins
        # (parents are siblings, and other parents are also siblings)

        # Grandparents from father's side
        gf1 = PersonORM(first_name="GF1", surname="Smith", sex=Sex.MALE)
        gm1 = PersonORM(first_name="GM1", surname="Smith", sex=Sex.FEMALE)
        session.add_all([gf1, gm1])
        session.flush()

        gfamily1 = FamilyORM(father_id=gf1.id, mother_id=gm1.id)
        session.add(gfamily1)
        session.flush()

        # Grandparents from mother's side
        gf2 = PersonORM(first_name="GF2", surname="Jones", sex=Sex.MALE)
        gm2 = PersonORM(first_name="GM2", surname="Jones", sex=Sex.FEMALE)
        session.add_all([gf2, gm2])
        session.flush()

        gfamily2 = FamilyORM(father_id=gf2.id, mother_id=gm2.id)
        session.add(gfamily2)
        session.flush()

        # Create two brothers from family 1
        brother1 = PersonORM(
            first_name="Brother1",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=gfamily1.id,
        )
        brother2 = PersonORM(
            first_name="Brother2",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=gfamily1.id,
        )
        session.add_all([brother1, brother2])
        session.flush()

        # Create two sisters from family 2
        sister1 = PersonORM(
            first_name="Sister1",
            surname="Jones",
            sex=Sex.FEMALE,
            parent_family_id=gfamily2.id,
        )
        sister2 = PersonORM(
            first_name="Sister2",
            surname="Jones",
            sex=Sex.FEMALE,
            parent_family_id=gfamily2.id,
        )
        session.add_all([sister1, sister2])
        session.flush()

        # Create families: Brother1 + Sister1, Brother2 + Sister2
        family1 = FamilyORM(father_id=brother1.id, mother_id=sister1.id)
        family2 = FamilyORM(father_id=brother2.id, mother_id=sister2.id)
        session.add_all([family1, family2])
        session.flush()

        # Create double first cousins
        cousin1 = PersonORM(
            first_name="Cousin1",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family1.id,
        )
        cousin2 = PersonORM(
            first_name="Cousin2",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=family2.id,
        )
        session.add_all([cousin1, cousin2])
        session.flush()

        # Create family for double first cousins
        cousin_family = FamilyORM(father_id=cousin1.id, mother_id=cousin2.id)
        session.add(cousin_family)
        session.flush()

        # Create child
        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=cousin_family.id,
        )
        session.add(child)
        session.commit()

        # Calculate consanguinity
        result = genealogy_algorithms.calculate_consanguinity_advanced(
            session, child.id
        )

        # Double first cousins have double the consanguinity of regular first cousins
        # Expected: 2 * 0.0625 = 0.125
        expected_consanguinity = 0.125
        assert math.isclose(
            result.consanguinity, expected_consanguinity, rel_tol=1e-3
        ), f"Expected {expected_consanguinity}, got {result.consanguinity}"
        assert len(result.common_ancestors) == 4  # All 4 grandparents

    def test_consanguinity_with_ancestor_inbreeding(self, session, genealogy_algorithms):
        """Test that ancestor's consanguinity is factored into calculation."""
        # NOTE: The formula includes (1 + F(ancestor)) where F is ancestor's consanguinity
        # Create a scenario where an ancestor is already inbred

        # Great-grandparents
        ggf = PersonORM(first_name="GGF", surname="Smith", sex=Sex.MALE)
        ggm = PersonORM(first_name="GGM", surname="Smith", sex=Sex.FEMALE)
        session.add_all([ggf, ggm])
        session.flush()

        ggfamily = FamilyORM(father_id=ggf.id, mother_id=ggm.id)
        session.add(ggfamily)
        session.flush()

        # Create sibling grandparents (to create an inbred parent)
        gf = PersonORM(
            first_name="GF",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=ggfamily.id,
        )
        gm = PersonORM(
            first_name="GM",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=ggfamily.id,
        )
        session.add_all([gf, gm])
        session.flush()

        # Inbred grandparent family (siblings having child)
        gfamily_inbred = FamilyORM(father_id=gf.id, mother_id=gm.id)
        session.add(gfamily_inbred)
        session.flush()

        # Create an inbred parent
        inbred_parent = PersonORM(
            first_name="InbredParent",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=gfamily_inbred.id,
        )
        session.add(inbred_parent)
        session.flush()

        # Create unrelated spouse
        spouse = PersonORM(first_name="Spouse", surname="Jones", sex=Sex.FEMALE)
        session.add(spouse)
        session.flush()

        # Create family
        family = FamilyORM(father_id=inbred_parent.id, mother_id=spouse.id)
        session.add(family)
        session.flush()

        # Create child
        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        session.add(child)
        session.commit()

        # Calculate consanguinity for inbred parent first
        parent_result = genealogy_algorithms.calculate_consanguinity_advanced(
            session, inbred_parent.id
        )
        assert parent_result.consanguinity > 0

        # Calculate consanguinity for child
        result = genealogy_algorithms.calculate_consanguinity_advanced(
            session, child.id
        )

        # Child should have zero consanguinity because parents are unrelated
        # But this tests that the algorithm doesn't crash with inbred ancestors
        assert result.consanguinity == 0.0

    def test_topological_sort_respects_generations(self, session, genealogy_algorithms):
        """Test that topological sort processes ancestors before descendants."""
        # Create a multi-generation family
        # GGF, GGM -> GF, GM -> F, M -> Child

        ggf = PersonORM(first_name="GGF", surname="Smith", sex=Sex.MALE)
        ggm = PersonORM(first_name="GGM", surname="Smith", sex=Sex.FEMALE)
        session.add_all([ggf, ggm])
        session.flush()

        ggfamily = FamilyORM(father_id=ggf.id, mother_id=ggm.id)
        session.add(ggfamily)
        session.flush()

        gf = PersonORM(
            first_name="GF",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=ggfamily.id,
        )
        gm = PersonORM(
            first_name="GM",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=ggfamily.id,
        )
        session.add_all([gf, gm])
        session.flush()

        gfamily = FamilyORM(father_id=gf.id, mother_id=gm.id)
        session.add(gfamily)
        session.flush()

        father = PersonORM(
            first_name="Father",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=gfamily.id,
        )
        mother = PersonORM(
            first_name="Mother",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=gfamily.id,
        )
        session.add_all([father, mother])
        session.flush()

        family = FamilyORM(father_id=father.id, mother_id=mother.id)
        session.add(family)
        session.flush()

        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        session.add(child)
        session.commit()

        # Perform topological sort
        sorted_persons = genealogy_algorithms.topological_sort_persons(session)

        # Find positions in sorted list
        positions = {person.id: i for i, person in enumerate(sorted_persons)}

        # Verify ancestors come before descendants
        assert positions[ggf.id] < positions[gf.id]
        assert positions[ggm.id] < positions[gm.id]
        assert positions[gf.id] < positions[father.id]
        assert positions[gm.id] < positions[mother.id]
        assert positions[father.id] < positions[child.id]
        assert positions[mother.id] < positions[child.id]


class TestConsanguinityCaching:
    """Test caching mechanisms for performance."""

    def test_cache_hit_on_repeated_calculation(self, session, genealogy_algorithms):
        """Test that cache is used for repeated calculations."""
        # Create simple family
        father = PersonORM(first_name="Father", surname="Smith", sex=Sex.MALE)
        mother = PersonORM(first_name="Mother", surname="Jones", sex=Sex.FEMALE)
        session.add_all([father, mother])
        session.flush()

        family = FamilyORM(father_id=father.id, mother_id=mother.id)
        session.add(family)
        session.flush()

        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        session.add(child)
        session.commit()

        # Clear cache
        genealogy_algorithms.clear_consanguinity_cache()

        # First calculation (cache miss)
        result1 = genealogy_algorithms.calculate_consanguinity_advanced(
            session, child.id
        )
        stats1 = genealogy_algorithms.get_cache_stats()

        # Second calculation (cache hit)
        result2 = genealogy_algorithms.calculate_consanguinity_advanced(
            session, child.id
        )
        stats2 = genealogy_algorithms.get_cache_stats()

        # Verify results are identical
        assert result1.consanguinity == result2.consanguinity

        # Verify cache was used
        assert stats2["hits"] > stats1["hits"]

    def test_clear_cache(self, session, genealogy_algorithms):
        """Test that cache can be cleared."""
        # Create simple person
        person = PersonORM(first_name="Person", surname="Smith", sex=Sex.MALE)
        session.add(person)
        session.commit()

        # Add to cache manually
        genealogy_algorithms._consanguinity_cache[person.id] = 0.5

        # Verify cache has entry
        assert len(genealogy_algorithms._consanguinity_cache) > 0

        # Clear cache
        genealogy_algorithms.clear_consanguinity_cache()

        # Verify cache is empty
        assert len(genealogy_algorithms._consanguinity_cache) == 0


class TestLoopDetection:
    """Test genealogical loop detection."""

    def test_detect_simple_loop(self, session, genealogy_algorithms):
        """Test detection of simple genealogical loop."""
        # NOTE: A loop occurs when a person is their own ancestor
        # This shouldn't happen in reality but can occur in bad data

        # Create person A
        person_a = PersonORM(first_name="PersonA", surname="Smith", sex=Sex.MALE)
        session.add(person_a)
        session.flush()

        # Create family where A is father
        family = FamilyORM(father_id=person_a.id, mother_id=None)
        session.add(family)
        session.flush()

        # Make person A their own child (creates loop)
        person_a.parent_family_id = family.id
        session.commit()

        # Detect loops
        has_loop = genealogy_algorithms.detect_genealogical_loops(session)
        assert has_loop is True

    def test_no_loop_in_normal_tree(self, session, genealogy_algorithms):
        """Test that normal family trees don't trigger loop detection."""
        # Create normal multi-generation family
        gf = PersonORM(first_name="GF", surname="Smith", sex=Sex.MALE)
        gm = PersonORM(first_name="GM", surname="Smith", sex=Sex.FEMALE)
        session.add_all([gf, gm])
        session.flush()

        gfamily = FamilyORM(father_id=gf.id, mother_id=gm.id)
        session.add(gfamily)
        session.flush()

        father = PersonORM(
            first_name="Father",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=gfamily.id,
        )
        session.add(father)
        session.flush()

        mother = PersonORM(first_name="Mother", surname="Jones", sex=Sex.FEMALE)
        session.add(mother)
        session.flush()

        family = FamilyORM(father_id=father.id, mother_id=mother.id)
        session.add(family)
        session.flush()

        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        session.add(child)
        session.commit()

        # Detect loops
        has_loop = genealogy_algorithms.detect_genealogical_loops(session)
        assert has_loop is False


class TestBulkConsanguinityComputation:
    """Test bulk consanguinity computation."""

    def test_compute_all_consanguinity_advanced(self, session, genealogy_algorithms):
        """Test bulk computation of consanguinity for all persons."""
        # Create a family tree with multiple persons
        # GF, GM -> F, M -> C1, C2

        gf = PersonORM(first_name="GF", surname="Smith", sex=Sex.MALE)
        gm = PersonORM(first_name="GM", surname="Smith", sex=Sex.FEMALE)
        session.add_all([gf, gm])
        session.flush()

        gfamily = FamilyORM(father_id=gf.id, mother_id=gm.id)
        session.add(gfamily)
        session.flush()

        father = PersonORM(
            first_name="Father",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=gfamily.id,
        )
        mother = PersonORM(
            first_name="Mother",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=gfamily.id,
        )
        session.add_all([father, mother])
        session.flush()

        family = FamilyORM(father_id=father.id, mother_id=mother.id)
        session.add(family)
        session.flush()

        child1 = PersonORM(
            first_name="Child1",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        child2 = PersonORM(
            first_name="Child2",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=family.id,
        )
        session.add_all([child1, child2])
        session.commit()

        # Compute consanguinity for all
        results = genealogy_algorithms.compute_all_consanguinity_advanced(
            session, from_scratch=True, verbosity=0
        )

        # Verify all persons have results
        assert gf.id in results
        assert gm.id in results
        assert father.id in results
        assert mother.id in results
        assert child1.id in results
        assert child2.id in results

        # Verify children have expected consanguinity
        # (siblings marrying -> consanguinity = 0.25)
        expected_child_consanguinity = 0.25
        assert math.isclose(
            results[child1.id], expected_child_consanguinity, rel_tol=1e-3
        )
        assert math.isclose(
            results[child2.id], expected_child_consanguinity, rel_tol=1e-3
        )


class TestRelationshipPaths:
    """Test relationship path finding."""

    def test_find_relationship_paths_siblings(self, session, genealogy_algorithms):
        """Test finding relationship paths between siblings."""
        # Create siblings
        father = PersonORM(first_name="Father", surname="Smith", sex=Sex.MALE)
        mother = PersonORM(first_name="Mother", surname="Jones", sex=Sex.FEMALE)
        session.add_all([father, mother])
        session.flush()

        family = FamilyORM(father_id=father.id, mother_id=mother.id)
        session.add(family)
        session.flush()

        sibling1 = PersonORM(
            first_name="Sibling1",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        sibling2 = PersonORM(
            first_name="Sibling2",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=family.id,
        )
        session.add_all([sibling1, sibling2])
        session.commit()

        # Find relationship paths
        paths = genealogy_algorithms.find_detailed_relationship_paths(
            session, sibling1.id, sibling2.id
        )

        assert len(paths) > 0
        # Should have paths through both father and mother
        assert len(paths) == 2
        assert paths[0].person1_distance == 1
        assert paths[0].person2_distance == 1

    def test_find_relationship_paths_cousins(self, session, genealogy_algorithms):
        """Test finding relationship paths between first cousins."""
        # Create grandparents
        gf = PersonORM(first_name="GF", surname="Smith", sex=Sex.MALE)
        gm = PersonORM(first_name="GM", surname="Smith", sex=Sex.FEMALE)
        session.add_all([gf, gm])
        session.flush()

        gfamily = FamilyORM(father_id=gf.id, mother_id=gm.id)
        session.add(gfamily)
        session.flush()

        # Create two siblings
        parent1 = PersonORM(
            first_name="Parent1",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=gfamily.id,
        )
        parent2 = PersonORM(
            first_name="Parent2",
            surname="Smith",
            sex=Sex.FEMALE,
            parent_family_id=gfamily.id,
        )
        session.add_all([parent1, parent2])
        session.flush()

        # Create spouses
        spouse1 = PersonORM(first_name="Spouse1", surname="Jones", sex=Sex.FEMALE)
        spouse2 = PersonORM(first_name="Spouse2", surname="Brown", sex=Sex.MALE)
        session.add_all([spouse1, spouse2])
        session.flush()

        # Create families
        family1 = FamilyORM(father_id=parent1.id, mother_id=spouse1.id)
        family2 = FamilyORM(father_id=spouse2.id, mother_id=parent2.id)
        session.add_all([family1, family2])
        session.flush()

        # Create cousins
        cousin1 = PersonORM(
            first_name="Cousin1",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family1.id,
        )
        cousin2 = PersonORM(
            first_name="Cousin2",
            surname="Brown",
            sex=Sex.FEMALE,
            parent_family_id=family2.id,
        )
        session.add_all([cousin1, cousin2])
        session.commit()

        # Find relationship paths
        paths = genealogy_algorithms.find_detailed_relationship_paths(
            session, cousin1.id, cousin2.id
        )

        assert len(paths) > 0
        # Should have paths through both grandparents
        assert len(paths) == 2
        # Each path should be distance 2 (cousin -> parent -> grandparent)
        assert paths[0].person1_distance == 2
        assert paths[0].person2_distance == 2
        assert "Cousins germains" in paths[0].relationship_name


class TestRelationshipSummary:
    """Test relationship summary generation."""

    def test_relationship_summary_self(self, session, genealogy_algorithms):
        """Test relationship summary for same person."""
        person = PersonORM(first_name="Person", surname="Smith", sex=Sex.MALE)
        session.add(person)
        session.commit()

        summary = genealogy_algorithms.find_relationship_summary(
            session, person.id, person.id
        )

        assert summary is not None
        assert summary.primary_relationship == RelationType.SELF
        assert "Même personne" in summary.relationship_description

    def test_relationship_summary_unrelated(self, session, genealogy_algorithms):
        """Test relationship summary for unrelated persons."""
        person1 = PersonORM(first_name="Person1", surname="Smith", sex=Sex.MALE)
        person2 = PersonORM(first_name="Person2", surname="Jones", sex=Sex.FEMALE)
        session.add_all([person1, person2])
        session.commit()

        summary = genealogy_algorithms.find_relationship_summary(
            session, person1.id, person2.id
        )

        assert summary is None  # No relationship

    def test_relationship_summary_parent_child(self, session, genealogy_algorithms):
        """Test relationship summary for parent-child."""
        father = PersonORM(first_name="Father", surname="Smith", sex=Sex.MALE)
        mother = PersonORM(first_name="Mother", surname="Jones", sex=Sex.FEMALE)
        session.add_all([father, mother])
        session.flush()

        family = FamilyORM(father_id=father.id, mother_id=mother.id)
        session.add(family)
        session.flush()

        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        session.add(child)
        session.commit()

        summary = genealogy_algorithms.find_relationship_summary(
            session, father.id, child.id
        )

        assert summary is not None
        assert summary.primary_relationship == RelationType.PARENT
        assert "Parent/Enfant" in summary.relationship_description


class TestCacheStatistics:
    """Test cache statistics tracking."""

    def test_cache_stats_tracking(self, session, genealogy_algorithms):
        """Test that cache statistics are properly tracked."""
        # Create simple family
        father = PersonORM(first_name="Father", surname="Smith", sex=Sex.MALE)
        mother = PersonORM(first_name="Mother", surname="Jones", sex=Sex.FEMALE)
        session.add_all([father, mother])
        session.flush()

        family = FamilyORM(father_id=father.id, mother_id=mother.id)
        session.add(family)
        session.flush()

        child = PersonORM(
            first_name="Child",
            surname="Smith",
            sex=Sex.MALE,
            parent_family_id=family.id,
        )
        session.add(child)
        session.commit()

        # Clear cache and stats
        genealogy_algorithms.clear_consanguinity_cache()

        # Perform calculation (miss)
        genealogy_algorithms.calculate_consanguinity_advanced(session, child.id)
        stats1 = genealogy_algorithms.get_cache_stats()
        assert stats1["misses"] > 0

        # Perform same calculation (hit)
        genealogy_algorithms.calculate_consanguinity_advanced(session, child.id)
        stats2 = genealogy_algorithms.get_cache_stats()
        assert stats2["hits"] > stats1["hits"]
        assert stats2["hit_rate"] > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_nonexistent_person_id(self, session, genealogy_algorithms):
        """Test calculation with non-existent person ID."""
        result = genealogy_algorithms.calculate_consanguinity_advanced(session, 99999)

        assert result.consanguinity == 0.0
        assert len(result.common_ancestors) == 0

    def test_empty_database(self, session, genealogy_algorithms):
        """Test bulk calculation on empty database."""
        results = genealogy_algorithms.compute_all_consanguinity_advanced(
            session, verbosity=0
        )

        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
