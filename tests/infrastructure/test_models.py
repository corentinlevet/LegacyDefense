"""
Tests pour les modèles de base de données (SQLAlchemy).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.geneweb.infrastructure.database import Base
from src.geneweb.infrastructure.models import (
    Genealogy,
    Person,
    Family,
    SexEnum,
)


@pytest.fixture
def test_engine():
    """Crée un moteur de base de données de test en mémoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Crée une session de test."""
    TestingSessionLocal = sessionmaker(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


class TestGenealogyModel:
    """Tests pour le modèle Genealogy."""

    def test_create_genealogy(self, test_session):
        """Test création d'une généalogie."""
        genealogy = Genealogy(name="Test Family")
        test_session.add(genealogy)
        test_session.commit()
        
        assert genealogy.id is not None
        assert genealogy.name == "Test Family"

    def test_genealogy_unique_name(self, test_session):
        """Test que le nom de généalogie doit être unique."""
        genealogy1 = Genealogy(name="Unique Name")
        test_session.add(genealogy1)
        test_session.commit()
        
        genealogy2 = Genealogy(name="Unique Name")
        test_session.add(genealogy2)
        
        with pytest.raises(Exception):  # IntegrityError attendu
            test_session.commit()

    def test_genealogy_with_persons_relationship(self, test_session):
        """Test relation entre généalogie et personnes."""
        genealogy = Genealogy(name="Family Tree")
        test_session.add(genealogy)
        test_session.commit()
        
        person1 = Person(
            genealogy_id=genealogy.id,
            first_name="John",
            surname="Doe",
            sex="M"
        )
        person2 = Person(
            genealogy_id=genealogy.id,
            first_name="Jane",
            surname="Doe",
            sex="F"
        )
        
        test_session.add(person1)
        test_session.add(person2)
        test_session.commit()
        
        # Rafraîchir la généalogie pour charger les relations
        test_session.refresh(genealogy)
        assert len(genealogy.persons) == 2

    def test_genealogy_cascade_delete(self, test_session):
        """Test que supprimer une généalogie supprime aussi ses personnes."""
        genealogy = Genealogy(name="Delete Test")
        test_session.add(genealogy)
        test_session.commit()
        
        person = Person(
            genealogy_id=genealogy.id,
            first_name="Test",
            surname="Person",
            sex="M"
        )
        test_session.add(person)
        test_session.commit()
        
        person_id = person.id
        
        # Supprimer la généalogie
        test_session.delete(genealogy)
        test_session.commit()
        
        # Vérifier que la personne est aussi supprimée
        deleted_person = test_session.query(Person).filter(Person.id == person_id).first()
        assert deleted_person is None


class TestPersonModel:
    """Tests pour le modèle Person."""

    def test_create_person_minimal(self, test_session):
        """Test création d'une personne avec données minimales."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        person = Person(
            genealogy_id=genealogy.id,
            first_name="John",
            surname="Doe",
            sex="M"
        )
        test_session.add(person)
        test_session.commit()
        
        assert person.id is not None
        assert person.first_name == "John"
        assert person.surname == "Doe"
        assert person.sex == "M"

    def test_create_person_complete(self, test_session):
        """Test création d'une personne avec toutes les données."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        person = Person(
            genealogy_id=genealogy.id,
            first_name="Marie",
            surname="Curie",
            sex="F",
            birth_date="07 NOV 1867",
            birth_place="Warsaw, Poland",
            death_date="04 JUL 1934",
            death_place="Passy, France",
            occupation="Physicist",
            notes="Nobel Prize winner",
            public_name="Marie Curie",
            qualifier="Dr.",
            alias="Madame Curie",
            baptism_date="10 NOV 1867",
            baptism_place="Warsaw",
            burial_date="10 JUL 1934",
            burial_place="Panthéon, Paris",
            access="public"
        )
        test_session.add(person)
        test_session.commit()
        
        assert person.id is not None
        assert person.occupation == "Physicist"
        assert person.notes == "Nobel Prize winner"
        assert person.public_name == "Marie Curie"

    def test_person_sex_values(self, test_session):
        """Test différentes valeurs de sexe."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        # Test sexe masculin
        male = Person(genealogy_id=genealogy.id, first_name="M", surname="Test", sex="M")
        test_session.add(male)
        
        # Test sexe féminin
        female = Person(genealogy_id=genealogy.id, first_name="F", surname="Test", sex="F")
        test_session.add(female)
        
        # Test sexe inconnu
        unknown = Person(genealogy_id=genealogy.id, first_name="U", surname="Test", sex="U")
        test_session.add(unknown)
        
        test_session.commit()
        
        assert male.sex == "M"
        assert female.sex == "F"
        assert unknown.sex == "U"

    def test_person_with_families_as_father(self, test_session):
        """Test personne comme père dans une famille."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        father = Person(genealogy_id=genealogy.id, first_name="Dad", surname="Test", sex="M")
        mother = Person(genealogy_id=genealogy.id, first_name="Mom", surname="Test", sex="F")
        test_session.add(father)
        test_session.add(mother)
        test_session.commit()
        
        family = Family(
            genealogy_id=genealogy.id,
            father_id=father.id,
            mother_id=mother.id,
            marriage_date="15 JUN 1990"
        )
        test_session.add(family)
        test_session.commit()
        
        test_session.refresh(father)
        assert len(father.families_as_father) == 1
        assert father.families_as_father[0].marriage_date == "15 JUN 1990"

    def test_person_with_families_as_mother(self, test_session):
        """Test personne comme mère dans une famille."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        father = Person(genealogy_id=genealogy.id, first_name="Dad", surname="Test", sex="M")
        mother = Person(genealogy_id=genealogy.id, first_name="Mom", surname="Test", sex="F")
        test_session.add(father)
        test_session.add(mother)
        test_session.commit()
        
        family = Family(
            genealogy_id=genealogy.id,
            father_id=father.id,
            mother_id=mother.id
        )
        test_session.add(family)
        test_session.commit()
        
        test_session.refresh(mother)
        assert len(mother.families_as_mother) == 1

    def test_person_indexing(self, test_session):
        """Test que les index sont correctement créés."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        # Créer plusieurs personnes
        for i in range(10):
            person = Person(
                genealogy_id=genealogy.id,
                first_name=f"First{i}",
                surname=f"Last{i}",
                sex="M"
            )
            test_session.add(person)
        
        test_session.commit()
        
        # Rechercher par prénom (devrait utiliser l'index)
        result = test_session.query(Person).filter(Person.first_name == "First5").first()
        assert result is not None
        assert result.first_name == "First5"


class TestFamilyModel:
    """Tests pour le modèle Family."""

    def test_create_family_minimal(self, test_session):
        """Test création d'une famille minimale."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        family = Family(genealogy_id=genealogy.id)
        test_session.add(family)
        test_session.commit()
        
        assert family.id is not None
        assert family.genealogy_id == genealogy.id

    def test_create_family_with_parents(self, test_session):
        """Test création d'une famille avec parents."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        father = Person(genealogy_id=genealogy.id, first_name="John", surname="Smith", sex="M")
        mother = Person(genealogy_id=genealogy.id, first_name="Jane", surname="Smith", sex="F")
        test_session.add(father)
        test_session.add(mother)
        test_session.commit()
        
        family = Family(
            genealogy_id=genealogy.id,
            father_id=father.id,
            mother_id=mother.id
        )
        test_session.add(family)
        test_session.commit()
        
        assert family.father_id == father.id
        assert family.mother_id == mother.id
        assert family.father.first_name == "John"
        assert family.mother.first_name == "Jane"

    def test_create_family_complete(self, test_session):
        """Test création d'une famille avec toutes les données."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        father = Person(genealogy_id=genealogy.id, first_name="Bob", surname="Brown", sex="M")
        mother = Person(genealogy_id=genealogy.id, first_name="Alice", surname="Brown", sex="F")
        test_session.add(father)
        test_session.add(mother)
        test_session.commit()
        
        family = Family(
            genealogy_id=genealogy.id,
            father_id=father.id,
            mother_id=mother.id,
            marriage_date="15 JUN 1990",
            marriage_place="Paris, France",
            divorce_date="10 DEC 2000",
            marriage_note="Civil ceremony",
            marriage_src="City Hall Records"
        )
        test_session.add(family)
        test_session.commit()
        
        assert family.marriage_date == "15 JUN 1990"
        assert family.marriage_place == "Paris, France"
        assert family.divorce_date == "10 DEC 2000"
        assert family.marriage_note == "Civil ceremony"
        assert family.marriage_src == "City Hall Records"

    def test_family_without_father(self, test_session):
        """Test famille sans père (mère célibataire)."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        mother = Person(genealogy_id=genealogy.id, first_name="Single", surname="Mom", sex="F")
        test_session.add(mother)
        test_session.commit()
        
        family = Family(
            genealogy_id=genealogy.id,
            mother_id=mother.id
        )
        test_session.add(family)
        test_session.commit()
        
        assert family.father_id is None
        assert family.mother_id == mother.id

    def test_family_without_mother(self, test_session):
        """Test famille sans mère."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        father = Person(genealogy_id=genealogy.id, first_name="Single", surname="Dad", sex="M")
        test_session.add(father)
        test_session.commit()
        
        family = Family(
            genealogy_id=genealogy.id,
            father_id=father.id
        )
        test_session.add(family)
        test_session.commit()
        
        assert family.father_id == father.id
        assert family.mother_id is None

    def test_family_relationships(self, test_session):
        """Test toutes les relations de la famille."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        father = Person(genealogy_id=genealogy.id, first_name="F", surname="T", sex="M")
        mother = Person(genealogy_id=genealogy.id, first_name="M", surname="T", sex="F")
        test_session.add(father)
        test_session.add(mother)
        test_session.commit()
        
        family = Family(
            genealogy_id=genealogy.id,
            father_id=father.id,
            mother_id=mother.id
        )
        test_session.add(family)
        test_session.commit()
        
        # Vérifier les relations
        assert family.genealogy.name == "Test"
        assert family.father.first_name == "F"
        assert family.mother.first_name == "M"


class TestSexEnum:
    """Tests pour l'énumération SexEnum."""

    def test_sex_enum_values(self):
        """Test les valeurs de l'énumération."""
        assert SexEnum.M.value == "M"
        assert SexEnum.F.value == "F"
        assert SexEnum.U.value == "U"

    def test_sex_enum_members(self):
        """Test les membres de l'énumération."""
        assert "M" in [e.value for e in SexEnum]
        assert "F" in [e.value for e in SexEnum]
        assert "U" in [e.value for e in SexEnum]

    def test_sex_enum_count(self):
        """Test le nombre de valeurs dans l'énumération."""
        assert len(SexEnum) == 3


class TestModelEdgeCases:
    """Tests des cas limites pour les modèles."""

    def test_person_with_empty_strings(self, test_session):
        """Test personne avec chaînes vides."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        person = Person(
            genealogy_id=genealogy.id,
            first_name="",
            surname="",
            sex=""
        )
        test_session.add(person)
        test_session.commit()
        
        assert person.first_name == ""
        assert person.surname == ""

    def test_person_with_very_long_text(self, test_session):
        """Test personne avec texte très long."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        long_text = "A" * 10000
        person = Person(
            genealogy_id=genealogy.id,
            first_name="Test",
            surname="Person",
            sex="M",
            notes=long_text
        )
        test_session.add(person)
        test_session.commit()
        
        assert len(person.notes) == 10000

    def test_multiple_families_same_parents(self, test_session):
        """Test plusieurs familles avec les mêmes parents (remariage)."""
        genealogy = Genealogy(name="Test")
        test_session.add(genealogy)
        test_session.commit()
        
        person1 = Person(genealogy_id=genealogy.id, first_name="P1", surname="T", sex="M")
        person2 = Person(genealogy_id=genealogy.id, first_name="P2", surname="T", sex="F")
        test_session.add(person1)
        test_session.add(person2)
        test_session.commit()
        
        # Première famille
        family1 = Family(
            genealogy_id=genealogy.id,
            father_id=person1.id,
            mother_id=person2.id,
            marriage_date="1990"
        )
        
        # Deuxième famille (remariage)
        family2 = Family(
            genealogy_id=genealogy.id,
            father_id=person1.id,
            mother_id=person2.id,
            marriage_date="2000"
        )
        
        test_session.add(family1)
        test_session.add(family2)
        test_session.commit()
        
        # Les deux familles doivent exister
        families = test_session.query(Family).filter(
            Family.father_id == person1.id,
            Family.mother_id == person2.id
        ).all()
        
        assert len(families) == 2

    def test_genealogy_with_special_characters_name(self, test_session):
        """Test généalogie avec caractères spéciaux."""
        special_names = [
            "Généalogie Française",
            "Family-Tree_2024",
            "Smith & Jones",
            "O'Connor Family",
            "Müller Familie"
        ]
        
        for name in special_names:
            genealogy = Genealogy(name=name)
            test_session.add(genealogy)
        
        test_session.commit()
        
        all_gen = test_session.query(Genealogy).all()
        assert len(all_gen) >= len(special_names)
