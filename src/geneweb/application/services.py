import os
import tempfile

from gedcom.element.family import FamilyElement
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser as GedcomParser
from sqlalchemy.orm import Session

from ..infrastructure.database import SessionLocal
from ..infrastructure.models import Event, Family, Genealogy, Person


class GenealogyService:
    def create_genealogy(self, name: str, force: bool = False):
        """
        Creates a new genealogy.

        :param name: The name of the genealogy.
        :param force: If True, deletes the existing genealogy and its data.
        """
        db: Session = SessionLocal()
        try:
            existing_genealogy = (
                db.query(Genealogy).filter(Genealogy.name == name).first()
            )

            if existing_genealogy:
                if not force:
                    print(
                        f"Genealogy '{name}' already exists. Use --force to overwrite."
                    )
                    return
                else:
                    print(f"Deleting existing genealogy '{name}'...")
                    db.delete(existing_genealogy)
                    db.commit()  # Commit the deletion

            print(f"Creating new genealogy '{name}'...")
            new_genealogy = Genealogy(name=name)
            db.add(new_genealogy)
            db.commit()
            print(f"Genealogy '{name}' created successfully.")
            return new_genealogy

        finally:
            db.close()

    def get_all_genealogies(self):
        """
        Retrieves all genealogies.
        """
        db: Session = SessionLocal()
        try:
            genealogies = db.query(Genealogy).all()
            return genealogies
        finally:
            db.close()

    def import_gedcom(self, genealogy_name: str, gedcom_content: str, db: Session):
        """
        Parses GEDCOM content and populates the database for a specific genealogy.
        """
        genealogy = db.query(Genealogy).filter(Genealogy.name == genealogy_name).first()
        if not genealogy:
            raise ValueError(f"Genealogy '{genealogy_name}' not found.")

        # Créer un fichier temporaire pour le parser GEDCOM
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ged", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(gedcom_content)
            tmp_file_path = tmp_file.name

        try:
            # Créer le parser et charger le contenu GEDCOM
            parser = GedcomParser()
            parser.parse_file(tmp_file_path)

            # Récupérer les individus et familles depuis le dictionnaire d'éléments
            element_dict = parser.get_element_dictionary()
            gedcom_individuals = {
                k: v
                for k, v in element_dict.items()
                if isinstance(v, IndividualElement)
            }
            gedcom_families = {
                k: v for k, v in element_dict.items() if isinstance(v, FamilyElement)
            }

            # Maps GEDCOM ID to our Person/Family object
            person_map = {}
            family_map = {}

            # --- Pass 1: Create Persons ---
            for gedcom_id, gedcom_indi in gedcom_individuals.items():
                first_name = ""
                surname = ""
                name_record = gedcom_indi.get_child_elements()
                for child in name_record:
                    if child.get_tag() == "NAME":
                        full_name = child.get_value()
                        parts = full_name.split("/")
                        if len(parts) == 3:  # e.g., Given /Surname/
                            first_name = parts[0].strip()
                            surname = parts[1].strip()
                        elif len(parts) == 2:  # e.g., /Surname/
                            surname = parts[1].strip() if parts[1] else parts[0].strip()
                        else:  # e.g., Full Name
                            first_name = full_name
                        break

                sex = "U"
                for child in gedcom_indi.get_child_elements():
                    if child.get_tag() == "SEX":
                        sex = child.get_value()
                        break

                person = Person(
                    genealogy_id=genealogy.id,
                    first_name=first_name,
                    surname=surname,
                    sex=sex,
                )
                db.add(person)
                person_map[gedcom_id] = person

            db.flush()  # Flush to assign IDs to persons

            # --- Pass 2: Add Person Details and Events ---
            for gedcom_id, gedcom_indi in gedcom_individuals.items():
                person = person_map[gedcom_id]

                for child_element in gedcom_indi.get_child_elements():
                    tag = child_element.get_tag()

                    # Birth Event
                    if tag == "BIRT":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        person.birth_date = date_val
                        person.birth_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                person_id=person.id,
                                event_type="BIRT",
                                date=date_val,
                                place=place_val,
                            )
                        )

                    # Death Event
                    elif tag == "DEAT":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        person.death_date = date_val
                        person.death_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                person_id=person.id,
                                event_type="DEAT",
                                date=date_val,
                                place=place_val,
                            )
                        )

                    # Occupation
                    elif tag == "OCCU":
                        person.occupation = child_element.get_value()

                    # Notes
                    elif tag == "NOTE":
                        person.notes = child_element.get_value()

                    # Baptism
                    elif tag == "BAPM":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        person.baptism_date = date_val
                        person.baptism_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                person_id=person.id,
                                event_type="BAPM",
                                date=date_val,
                                place=place_val,
                            )
                        )

                    # Burial
                    elif tag == "BURI":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        person.burial_date = date_val
                        person.burial_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                person_id=person.id,
                                event_type="BURI",
                                date=date_val,
                                place=place_val,
                            )
                        )

            # --- Pass 3: Create Families and link members ---
            for gedcom_id, gedcom_fam in gedcom_families.items():
                husband_id = None
                wife_id = None

                for child in gedcom_fam.get_child_elements():
                    if child.get_tag() == "HUSB":
                        husband_id = child.get_value()
                    elif child.get_tag() == "WIFE":
                        wife_id = child.get_value()

                family = Family(
                    genealogy_id=genealogy.id,
                    father_id=(
                        person_map[husband_id].id
                        if husband_id and husband_id in person_map
                        else None
                    ),
                    mother_id=(
                        person_map[wife_id].id
                        if wife_id and wife_id in person_map
                        else None
                    ),
                )
                db.add(family)
                family_map[gedcom_id] = family

            db.flush()  # Flush to assign IDs to families

            # --- Pass 4: Add Family Details and Events, link children ---
            for gedcom_id, gedcom_fam in gedcom_families.items():
                family = family_map[gedcom_id]

                for child_element in gedcom_fam.get_child_elements():
                    tag = child_element.get_tag()

                    # Marriage Event
                    if tag == "MARR":
                        date_val = None
                        place_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()
                            elif sub_child.get_tag() == "PLAC":
                                place_val = sub_child.get_value()

                        family.marriage_date = date_val
                        family.marriage_place = place_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                family_id=family.id,
                                event_type="MARR",
                                date=date_val,
                                place=place_val,
                            )
                        )

                    # Divorce Event
                    elif tag == "DIV":
                        date_val = None
                        for sub_child in child_element.get_child_elements():
                            if sub_child.get_tag() == "DATE":
                                date_val = sub_child.get_value()

                        family.divorce_date = date_val
                        db.add(
                            Event(
                                genealogy_id=genealogy.id,
                                family_id=family.id,
                                event_type="DIV",
                                date=date_val,
                            )
                        )

                    # Children
                    elif tag == "CHIL":
                        child_id = child_element.get_value()
                        if child_id and child_id in person_map:
                            family.children.append(person_map[child_id])

            db.commit()
            print(f"GEDCOM content imported into genealogy '{genealogy.name}'.")
        finally:
            # Supprimer le fichier temporaire
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
