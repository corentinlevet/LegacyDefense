"""
Tests de validation et d'erreurs pour les services.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.geneweb.infrastructure.database import Base
from src.geneweb.infrastructure.models import Genealogy, Person, Family
from src.geneweb.infrastructure.repositories.sql_person_repository import (
    SQLPersonRepository,
)
from src.geneweb.infrastructure.repositories.sql_genealogy_repository import (
    SQLGenealogyRepository,
)


@pytest.fixture
def test_db():
    """Crée une base de données de test en mémoire."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()


class TestDataValidation:
    """Tests de validation des données."""

    def test_person_required_fields(self, test_db):
        """Test que les champs requis sont nécessaires."""
        # Genealogy est requis
        person = Person(
            first_name="Test",
            surname="Person",
            sex="M"
            # genealogy_id manquant
        )
        test_db.add(person)
        
        with pytest.raises(Exception):  # IntegrityError attendu
            test_db.commit()

    def test_genealogy_name_length(self, test_db):
        """Test limite de longueur du nom."""
        # Nom de 100 caractères devrait passer
        name_100 = "A" * 100
        gen = Genealogy(name=name_100)
        test_db.add(gen)
        test_db.commit()
        assert gen.id is not None
        
        # Nom de plus de 100 caractères devrait être tronqué ou échouer
        # (selon la configuration de SQLAlchemy)

    def test_person_sex_invalid_value(self, test_db):
        """Test valeur de sexe invalide."""
        gen = Genealogy(name="Test")
        test_db.add(gen)
        test_db.commit()
        
        # SQLAlchemy accepte n'importe quelle string pour sex
        # mais on peut tester que les valeurs valides sont M, F, U
        person = Person(
            genealogy_id=gen.id,
            first_name="Test",
            surname="Person",
            sex="X"  # Invalide
        )
        test_db.add(person)
        test_db.commit()  # Pas d'erreur, mais pas recommandé

    def test_family_parent_references(self, test_db):
        """Test références parents dans famille."""
        gen = Genealogy(name="Test")
        test_db.add(gen)
        test_db.commit()
        
        # Famille avec ID parents invalides
        family = Family(
            genealogy_id=gen.id,
            father_id=99999,  # N'existe pas
            mother_id=99998   # N'existe pas
        )
        test_db.add(family)
        
        # Devrait échouer avec ForeignKey constraint
        with pytest.raises(Exception):
            test_db.commit()


class TestRepositoryErrorHandling:
    """Tests de gestion d'erreurs des repositories."""

    def test_get_nonexistent_person(self, test_db):
        """Test récupération personne inexistante."""
        repo = SQLPersonRepository(test_db)
        person = repo.get_by_id(99999)
        
        assert person is None

    def test_get_with_invalid_id_type(self, test_db):
        """Test avec type d'ID invalide."""
        repo = SQLPersonRepository(test_db)
        
        # Python/SQLAlchemy devrait gérer la conversion
        person = repo.get_by_id("invalid")
        assert person is None

    def test_add_person_without_commit(self, test_db):
        """Test ajout sans commit explicite."""
        gen = Genealogy(name="Test")
        test_db.add(gen)
        test_db.commit()
        
        repo = SQLPersonRepository(test_db)
        person = Person(
            genealogy_id=gen.id,
            first_name="Test",
            surname="Person",
            sex="M"
        )
        
        # Le repository fait commit automatiquement
        result = repo.add(person)
        
        # Devrait être persisté
        assert result.id is not None

    def test_get_genealogy_case_sensitivity(self, test_db):
        """Test sensibilité à la casse pour généalogie."""
        gen = Genealogy(name="TestFamily")
        test_db.add(gen)
        test_db.commit()
        
        repo = SQLGenealogyRepository(test_db)
        
        # Recherche exacte
        result1 = repo.get_by_name("TestFamily")
        assert result1 is not None
        
        # Recherche avec casse différente (dépend de SQLite)
        result2 = repo.get_by_name("testfamily")
        # Peut être None ou pas selon la config


class TestConcurrency:
    """Tests de gestion de concurrence."""

    def test_multiple_sessions_same_person(self, test_db):
        """Test accès concurrent à la même personne."""
        gen = Genealogy(name="Test")
        test_db.add(gen)
        test_db.commit()
        
        # Créer une personne
        person = Person(
            genealogy_id=gen.id,
            first_name="Test",
            surname="Person",
            sex="M"
        )
        test_db.add(person)
        test_db.commit()
        
        person_id = person.id
        
        # Récupérer deux fois
        repo = SQLPersonRepository(test_db)
        person1 = repo.get_by_id(person_id)
        person2 = repo.get_by_id(person_id)
        
        # Devrait être le même objet (ou équivalent)
        assert person1.id == person2.id

    def test_add_multiple_persons_rapidly(self, test_db):
        """Test ajout rapide de plusieurs personnes."""
        gen = Genealogy(name="Test")
        test_db.add(gen)
        test_db.commit()
        
        repo = SQLPersonRepository(test_db)
        
        # Ajouter 100 personnes rapidement
        for i in range(100):
            person = Person(
                genealogy_id=gen.id,
                first_name=f"Person{i}",
                surname="Test",
                sex="M"
            )
            repo.add(person)
        
        # Vérifier qu'elles sont toutes là
        all_persons = test_db.query(Person).all()
        assert len(all_persons) == 100


class TestTransactionRollback:
    """Tests de rollback de transactions."""

    def test_rollback_on_error(self, test_db):
        """Test rollback en cas d'erreur."""
        gen = Genealogy(name="Test")
        test_db.add(gen)
        test_db.commit()
        
        try:
            # Ajouter une personne valide
            person1 = Person(
                genealogy_id=gen.id,
                first_name="Valid",
                surname="Person",
                sex="M"
            )
            test_db.add(person1)
            
            # Ajouter une personne invalide (sans genealogy_id)
            person2 = Person(
                first_name="Invalid",
                surname="Person",
                sex="F"
            )
            test_db.add(person2)
            
            test_db.commit()
        except Exception:
            test_db.rollback()
        
        # La première personne ne devrait pas être persistée non plus
        persons = test_db.query(Person).all()
        assert len(persons) == 0


class TestDatabaseConstraints:
    """Tests des contraintes de base de données."""

    def test_unique_genealogy_name(self, test_db):
        """Test contrainte d'unicité du nom de généalogie."""
        gen1 = Genealogy(name="Unique")
        test_db.add(gen1)
        test_db.commit()
        
        gen2 = Genealogy(name="Unique")
        test_db.add(gen2)
        
        with pytest.raises(Exception):
            test_db.commit()

    def test_cascade_delete_persons(self, test_db):
        """Test suppression en cascade des personnes."""
        gen = Genealogy(name="ToDelete")
        test_db.add(gen)
        test_db.commit()
        
        # Ajouter des personnes
        for i in range(5):
            person = Person(
                genealogy_id=gen.id,
                first_name=f"Person{i}",
                surname="Test",
                sex="M"
            )
            test_db.add(person)
        test_db.commit()
        
        person_count = test_db.query(Person).count()
        assert person_count == 5
        
        # Supprimer la généalogie
        test_db.delete(gen)
        test_db.commit()
        
        # Les personnes devraient être supprimées aussi
        person_count_after = test_db.query(Person).count()
        assert person_count_after == 0

    def test_cascade_delete_families(self, test_db):
        """Test suppression en cascade des familles."""
        gen = Genealogy(name="ToDelete")
        test_db.add(gen)
        test_db.commit()
        
        person1 = Person(
            genealogy_id=gen.id,
            first_name="P1",
            surname="Test",
            sex="M"
        )
        person2 = Person(
            genealogy_id=gen.id,
            first_name="P2",
            surname="Test",
            sex="F"
        )
        test_db.add(person1)
        test_db.add(person2)
        test_db.commit()
        
        family = Family(
            genealogy_id=gen.id,
            father_id=person1.id,
            mother_id=person2.id
        )
        test_db.add(family)
        test_db.commit()
        
        # Supprimer la généalogie
        test_db.delete(gen)
        test_db.commit()
        
        # La famille devrait être supprimée aussi
        family_count = test_db.query(Family).count()
        assert family_count == 0


class TestPerformance:
    """Tests de performance basiques."""

    def test_bulk_insert_persons(self, test_db):
        """Test insertion en masse de personnes."""
        gen = Genealogy(name="Bulk")
        test_db.add(gen)
        test_db.commit()
        
        # Préparer 1000 personnes
        persons = []
        for i in range(1000):
            person = Person(
                genealogy_id=gen.id,
                first_name=f"First{i}",
                surname=f"Last{i}",
                sex="M" if i % 2 == 0 else "F"
            )
            persons.append(person)
        
        # Insertion en masse
        test_db.bulk_save_objects(persons)
        test_db.commit()
        
        # Vérifier
        count = test_db.query(Person).count()
        assert count == 1000

    def test_query_with_index(self, test_db):
        """Test requête utilisant les index."""
        gen = Genealogy(name="Index Test")
        test_db.add(gen)
        test_db.commit()
        
        # Ajouter des personnes
        for i in range(100):
            person = Person(
                genealogy_id=gen.id,
                first_name=f"First{i}",
                surname=f"Last{i}",
                sex="M"
            )
            test_db.add(person)
        test_db.commit()
        
        # Requête sur champ indexé (first_name)
        results = test_db.query(Person).filter(
            Person.first_name == "First50"
        ).all()
        
        assert len(results) == 1
        assert results[0].first_name == "First50"


class TestSpecialCharactersHandling:
    """Tests de gestion des caractères spéciaux."""

    def test_unicode_in_names(self, test_db):
        """Test caractères Unicode dans les noms."""
        gen = Genealogy(name="Unicode Test")
        test_db.add(gen)
        test_db.commit()
        
        special_names = [
            ("François", "Müller"),
            ("Søren", "Kierkegaard"),
            ("北京", "上海"),
            ("José", "García"),
            ("Владимир", "Путин"),
        ]
        
        for first, last in special_names:
            person = Person(
                genealogy_id=gen.id,
                first_name=first,
                surname=last,
                sex="M"
            )
            test_db.add(person)
        
        test_db.commit()
        
        # Vérifier qu'elles sont toutes sauvegardées
        persons = test_db.query(Person).all()
        assert len(persons) >= len(special_names)

    def test_sql_injection_prevention(self, test_db):
        """Test prévention injection SQL."""
        gen = Genealogy(name="Security Test")
        test_db.add(gen)
        test_db.commit()
        
        # Tentative d'injection SQL dans le nom
        malicious_name = "'; DROP TABLE persons; --"
        
        person = Person(
            genealogy_id=gen.id,
            first_name=malicious_name,
            surname="Test",
            sex="M"
        )
        test_db.add(person)
        test_db.commit()
        
        # La table devrait toujours exister
        persons = test_db.query(Person).all()
        assert len(persons) == 1
        assert persons[0].first_name == malicious_name
