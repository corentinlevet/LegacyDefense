#!/usr/bin/env python3
"""
Test Data Generator for GeneWeb-Python
Generates realistic genealogical test data for testing and demonstration.
"""

from sqlalchemy.orm import Session
from typing import Optional
import random

from core.database import DatabaseManager, PersonORM, FamilyORM, DateORM, PlaceORM, EventORM
from core.models import Date, Sex, Access, EventType, DatePrecision


class TestDataGenerator:
    """Generate comprehensive test data for genealogical database."""
    
    def __init__(self):
        self.first_names_male = ["John", "Robert", "David", "Michael", "James", "William", "Peter", "Thomas", "Charles", "Richard"]
        self.first_names_female = ["Mary", "Elizabeth", "Sarah", "Margaret", "Emma", "Catherine", "Jane", "Anne", "Helen", "Alice"]
        self.surnames = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson"]
        self.places = ["London, England", "Manchester, England", "Birmingham, England", "Liverpool, England", "Leeds, England", "Bristol, England"]
        self.occupations = ["Teacher", "Engineer", "Doctor", "Carpenter", "Nurse", "Farmer", "Merchant", "Clerk", "Policeman", "Mechanic"]
    
    def create_person_with_events(self, session: Session, first_name: str, surname: str, 
                                  sex: Sex, birth_date: Date, birth_place: str = None,
                                  death_date: Date = None, death_place: str = None, occupation: str = "", 
                                  parent_family_id: int = None, access: Access = Access.PUBLIC) -> PersonORM:
        """Create a person with birth/death events using proper database schema."""
        
        # Create person
        person = PersonORM(
            first_name=first_name,
            surname=surname,
            sex=sex,
            occupation=occupation,
            parent_family_id=parent_family_id,
            access=access.value  # Use the enum value
        )
        session.add(person)
        session.flush()  # Get person ID
        
        # Create birth date object
        birth_date_obj = DateORM(
            day=birth_date.day,
            month=birth_date.month,
            year=birth_date.year,
            precision=DatePrecision.SURE
        )
        session.add(birth_date_obj)
        session.flush()
        
        # Create birth place object if provided
        birth_place_obj = None
        if birth_place:
            birth_place_obj = PlaceORM(place=birth_place)
            session.add(birth_place_obj)
            session.flush()
        
        # Create birth event
        birth_event = EventORM(
            event_type=EventType.BIRTH,
            birth_person_id=person.id,
            date_id=birth_date_obj.id,
            place_id=birth_place_obj.id if birth_place_obj else None
        )
        session.add(birth_event)
        
        # Create death event if provided
        if death_date:
            # Create death date object
            death_date_obj = DateORM(
                day=death_date.day,
                month=death_date.month,
                year=death_date.year,
                precision=DatePrecision.SURE
            )
            session.add(death_date_obj)
            session.flush()
            
            # Create death place object if provided
            death_place_obj = None
            if death_place:
                death_place_obj = PlaceORM(place=death_place)
                session.add(death_place_obj)
                session.flush()
            
            death_event = EventORM(
                event_type=EventType.DEATH,
                death_person_id=person.id,
                date_id=death_date_obj.id,
                place_id=death_place_obj.id if death_place_obj else None
            )
            session.add(death_event)
        
        return person
    
    def create_sample_family(self, session: Session) -> dict:
        """Create a comprehensive sample family for testing."""
        
        # Create the eldest generation (great-grandparents)
        john_smith_sr = self.create_person_with_events(
            session, "John", "Smith", Sex.MALE,
            Date(day=15, month=3, year=1920), "London, England",
            Date(day=22, month=8, year=1995), "London, England",
            "Carpenter", None, Access.PUBLIC
        )
        
        mary_johnson = self.create_person_with_events(
            session, "Mary", "Johnson", Sex.FEMALE,
            Date(day=8, month=7, year=1922), "Birmingham, England",
            Date(day=14, month=12, year=1998), "London, England",
            "", None, Access.PUBLIC
        )
        
        # Create their family
        family_1920 = FamilyORM(
            father_id=john_smith_sr.id,
            mother_id=mary_johnson.id
        )
        session.add(family_1920)
        session.flush()
        
        # Create middle generation (grandparents)
        robert_smith = self.create_person_with_events(
            session, "Robert", "Smith", Sex.MALE,
            Date(day=5, month=11, year=1945), "London, England",
            Date(day=18, month=4, year=2020), "Manchester, England",
            "Engineer", family_1920.id, Access.PUBLIC
        )
        
        elizabeth_brown = self.create_person_with_events(
            session, "Elizabeth", "Brown", Sex.FEMALE,
            Date(day=23, month=1, year=1948), "Liverpool, England",
            None, None, "Teacher", None, Access.PUBLIC
        )
        
        # Create family for middle generation
        family_1970 = FamilyORM(
            father_id=robert_smith.id,
            mother_id=elizabeth_brown.id
        )
        session.add(family_1970)
        session.flush()
        
        # Create current generation (parents)
        david_smith = self.create_person_with_events(
            session, "David", "Smith", Sex.MALE,
            Date(day=12, month=9, year=1975), "Manchester, England",
            None, None, "Software Developer", family_1970.id, Access.PUBLIC
        )
        
        sarah_wilson = self.create_person_with_events(
            session, "Sarah", "Wilson", Sex.FEMALE,
            Date(day=3, month=4, year=1978), "Leeds, England",
            None, None, "Doctor", None, Access.PUBLIC
        )
        
        # Create family for current generation
        family_2000 = FamilyORM(
            father_id=david_smith.id,
            mother_id=sarah_wilson.id
        )
        session.add(family_2000)
        session.flush()
        
        # Create children (youngest generation)
        michael_smith = self.create_person_with_events(
            session, "Michael", "Smith", Sex.MALE,
            Date(day=8, month=12, year=2005), "Manchester, England",
            None, None, "", family_2000.id, Access.PRIVATE
        )
        
        emma_smith = self.create_person_with_events(
            session, "Emma", "Smith", Sex.FEMALE,
            Date(day=19, month=7, year=2008), "Manchester, England",
            None, None, "", family_2000.id, Access.PRIVATE
        )
        
        session.commit()
        
        return {
            "great_grandparents": [john_smith_sr.id, mary_johnson.id],
            "grandparents": [robert_smith.id, elizabeth_brown.id],
            "parents": [david_smith.id, sarah_wilson.id],
            "children": [michael_smith.id, emma_smith.id],
        }
    
    def generate_random_families(self, session: Session, num_families: int = 5) -> list:
        """Generate random families for testing."""
        families = []
        
        for i in range(num_families):
            # Random father
            father_name = random.choice(self.first_names_male)
            father_surname = random.choice(self.surnames)
            father = self.create_person_with_events(
                session, father_name, father_surname, Sex.MALE,
                Date(day=random.randint(1, 28), month=random.randint(1, 12), year=random.randint(1950, 1990)),
                random.choice(self.places), None, None,
                random.choice(self.occupations), None, Access.PUBLIC
            )
            
            # Random mother
            mother_name = random.choice(self.first_names_female)
            mother_surname = random.choice(self.surnames)
            mother = self.create_person_with_events(
                session, mother_name, mother_surname, Sex.FEMALE,
                Date(day=random.randint(1, 28), month=random.randint(1, 12), year=random.randint(1950, 1990)),
                random.choice(self.places), None, None,
                random.choice(self.occupations), None, Access.PUBLIC
            )
            
            # Create family
            family = FamilyORM(
                father_id=father.id,
                mother_id=mother.id
            )
            session.add(family)
            session.flush()
            
            # Create 1-3 children
            num_children = random.randint(1, 3)
            children_ids = []
            
            for j in range(num_children):
                child_sex = random.choice([Sex.MALE, Sex.FEMALE])
                child_name = random.choice(self.first_names_male if child_sex == Sex.MALE else self.first_names_female)
                
                child = self.create_person_with_events(
                    session, child_name, father_surname, child_sex,
                    Date(day=random.randint(1, 28), month=random.randint(1, 12), year=random.randint(2000, 2020)),
                    random.choice(self.places), None, None,
                    "", family.id, Access.PRIVATE
                )
                children_ids.append(child.id)
            
            families.append({
                "family_id": family.id,
                "father_id": father.id,
                "mother_id": mother.id,
                "children_ids": children_ids
            })
        
        session.commit()
        return families


def populate_test_database():
    """Populate the database with comprehensive test data."""
    # Create database manager
    db_manager = DatabaseManager()
    
    # Create tables
    db_manager.create_tables()
    
    # Get database session
    session = db_manager.get_session()
    
    try:
        print("Creating test data generator...")
        generator = TestDataGenerator()
        
        print("Creating sample family...")
        family_ids = generator.create_sample_family(session)
        print(f"Created sample family with IDs: {family_ids}")
        
        print("Creating random families...")
        random_families = generator.generate_random_families(session, 3)
        print(f"Created {len(random_families)} random families")
        
        print("Test data population completed successfully!")
        
    except Exception as e:
        print(f"Error during test data generation: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    populate_test_database()