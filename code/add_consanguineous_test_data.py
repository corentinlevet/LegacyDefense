#!/usr/bin/env python3
"""
Script pour ajouter des données de test avec consanguinité à la base de données.

Ce script crée une famille avec plusieurs niveaux de consanguinité :
- Consanguinité proche (cousins germains)
- Consanguinité moyenne (cousins issus de germains)  
- Consanguinité lointaine (arrière-cousins)
"""

import sys
import os
from sqlalchemy.orm import Session

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import DatabaseManager, PersonORM, FamilyORM, DateORM, PlaceORM, EventORM
from core.models import Sex, EventType, MarriageType, DatePrecision, Calendar


def create_test_date(year: int, month: int = None, day: int = None) -> DateORM:
    """Créer une date de test."""
    return DateORM(
        year=year,
        month=month,
        day=day,
        precision=DatePrecision.SURE,
        calendar=Calendar.GREGORIAN
    )


def create_test_place(town: str, country: str = "France") -> PlaceORM:
    """Créer un lieu de test."""
    return PlaceORM(
        town=town,
        country=country
    )


def add_consanguineous_family(session: Session):
    """
    Ajouter une famille avec différents niveaux de consanguinité.
    
    Structure créée :
    - Ancêtres communs (Génération 1)
    - Leurs enfants (Génération 2) 
    - Petits-enfants qui se marient entre cousins (Génération 3)
    - Arrière-petits-enfants avec consanguinité (Génération 4)
    """
    
    print("Création des données de test avec consanguinité...")
    
    # ==========================================
    # GÉNÉRATION 1 - ANCÊTRES COMMUNS
    # ==========================================
    
    # Dates et lieux
    birth_1850 = create_test_date(1850)
    birth_1852 = create_test_date(1852)
    death_1920 = create_test_date(1920)
    death_1925 = create_test_date(1925)
    
    paris = create_test_place("Paris")
    lyon = create_test_place("Lyon")
    marseille = create_test_place("Marseille")
    
    session.add(birth_1850)
    session.add(birth_1852)
    session.add(death_1920)
    session.add(death_1925)
    session.add(paris)
    session.add(lyon)
    session.add(marseille)
    session.commit()
    
    # Ancêtre commun masculin - Jean DUBOIS
    jean_dubois = PersonORM(
        first_name="Jean",
        surname="DUBOIS",
        sex=Sex.MALE,
        occupation="Agriculteur",
        notes="Ancêtre commun de la famille - source de consanguinité"
    )
    session.add(jean_dubois)
    session.commit()
    
    # Ancêtre commun féminin - Marie MARTIN
    marie_martin = PersonORM(
        first_name="Marie",
        surname="MARTIN",
        sex=Sex.FEMALE,
        occupation="Ménagère",
        notes="Ancêtre commun de la famille - source de consanguinité"
    )
    session.add(marie_martin)
    session.commit()
    
    # Événements de naissance pour les ancêtres
    jean_birth = EventORM(
        event_type=EventType.BIRTH,
        birth_person_id=jean_dubois.id,
        date_id=birth_1850.id,
        place_id=paris.id,
        note="Naissance de l'ancêtre commun"
    )
    
    marie_birth = EventORM(
        event_type=EventType.BIRTH,
        birth_person_id=marie_martin.id,
        date_id=birth_1852.id,
        place_id=paris.id,
        note="Naissance de l'ancêtre commun"
    )
    
    session.add(jean_birth)
    session.add(marie_birth)
    session.commit()
    
    # Famille des ancêtres communs
    family_ancestors = FamilyORM(
        father_id=jean_dubois.id,
        mother_id=marie_martin.id,
        marriage=MarriageType.MARRIED,
        notes="Famille fondatrice - source de la consanguinité"
    )
    session.add(family_ancestors)
    session.commit()
    
    # ==========================================
    # GÉNÉRATION 2 - ENFANTS DES ANCÊTRES
    # ==========================================
    
    birth_1875 = create_test_date(1875)
    birth_1877 = create_test_date(1877)
    birth_1880 = create_test_date(1880)
    birth_1882 = create_test_date(1882)
    
    session.add(birth_1875)
    session.add(birth_1877)
    session.add(birth_1880)
    session.add(birth_1882)
    session.commit()
    
    # Fils 1 - Pierre DUBOIS
    pierre_dubois = PersonORM(
        first_name="Pierre",
        surname="DUBOIS",
        sex=Sex.MALE,
        parent_family_id=family_ancestors.id,
        occupation="Forgeron",
        notes="Fils des ancêtres communs - branche paternelle"
    )
    session.add(pierre_dubois)
    session.commit()
    
    pierre_birth = EventORM(
        event_type=EventType.BIRTH,
        birth_person_id=pierre_dubois.id,
        date_id=birth_1875.id,
        place_id=lyon.id
    )
    session.add(pierre_birth)
    
    # Fils 2 - Paul DUBOIS
    paul_dubois = PersonORM(
        first_name="Paul",
        surname="DUBOIS",
        sex=Sex.MALE,
        parent_family_id=family_ancestors.id,
        occupation="Menuisier",
        notes="Fils des ancêtres communs - branche paternelle"
    )
    session.add(paul_dubois)
    session.commit()
    
    paul_birth = EventORM(
        event_type=EventType.BIRTH,
        birth_person_id=paul_dubois.id,
        date_id=birth_1877.id,
        place_id=lyon.id
    )
    session.add(paul_birth)
    
    # Fille 1 - Jeanne DUBOIS
    jeanne_dubois = PersonORM(
        first_name="Jeanne",
        surname="DUBOIS",
        sex=Sex.FEMALE,
        parent_family_id=family_ancestors.id,
        occupation="Couturière",
        notes="Fille des ancêtres communs - branche maternelle"
    )
    session.add(jeanne_dubois)
    session.commit()
    
    jeanne_birth = EventORM(
        event_type=EventType.BIRTH,
        birth_person_id=jeanne_dubois.id,
        date_id=birth_1880.id,
        place_id=marseille.id
    )
    session.add(jeanne_birth)
    
    # Fille 2 - Louise DUBOIS
    louise_dubois = PersonORM(
        first_name="Louise",
        surname="DUBOIS",
        sex=Sex.FEMALE,
        parent_family_id=family_ancestors.id,
        occupation="Institutrice",
        notes="Fille des ancêtres communs - branche maternelle"
    )
    session.add(louise_dubois)
    session.commit()
    
    louise_birth = EventORM(
        event_type=EventType.BIRTH,
        birth_person_id=louise_dubois.id,
        date_id=birth_1882.id,
        place_id=marseille.id
    )
    session.add(louise_birth)
    session.commit()
    
    # Conjoints pour la génération 2 (non apparentés)
    
    # Épouse de Pierre - Catherine LECLERC
    catherine_leclerc = PersonORM(
        first_name="Catherine",
        surname="LECLERC",
        sex=Sex.FEMALE,
        occupation="Ménagère",
        notes="Épouse de Pierre DUBOIS - non apparentée"
    )
    session.add(catherine_leclerc)
    session.commit()
    
    # Épouse de Paul - Marguerite BERNARD
    marguerite_bernard = PersonORM(
        first_name="Marguerite",
        surname="BERNARD",
        sex=Sex.FEMALE,
        occupation="Ménagère",
        notes="Épouse de Paul DUBOIS - non apparentée"
    )
    session.add(marguerite_bernard)
    session.commit()
    
    # Époux de Jeanne - Henri ROUSSEAU
    henri_rousseau = PersonORM(
        first_name="Henri",
        surname="ROUSSEAU",
        sex=Sex.MALE,
        occupation="Négociant",
        notes="Époux de Jeanne DUBOIS - non apparenté"
    )
    session.add(henri_rousseau)
    session.commit()
    
    # Époux de Louise - François MOREAU
    francois_moreau = PersonORM(
        first_name="François",
        surname="MOREAU",
        sex=Sex.MALE,
        occupation="Pharmacien",
        notes="Époux de Louise DUBOIS - non apparenté"
    )
    session.add(francois_moreau)
    session.commit()
    
    # Familles de la génération 2
    family_pierre = FamilyORM(
        father_id=pierre_dubois.id,
        mother_id=catherine_leclerc.id,
        marriage=MarriageType.MARRIED,
        notes="Famille Pierre DUBOIS - Catherine LECLERC"
    )
    
    family_paul = FamilyORM(
        father_id=paul_dubois.id,
        mother_id=marguerite_bernard.id,
        marriage=MarriageType.MARRIED,
        notes="Famille Paul DUBOIS - Marguerite BERNARD"
    )
    
    family_jeanne = FamilyORM(
        father_id=henri_rousseau.id,
        mother_id=jeanne_dubois.id,
        marriage=MarriageType.MARRIED,
        notes="Famille Henri ROUSSEAU - Jeanne DUBOIS"
    )
    
    family_louise = FamilyORM(
        father_id=francois_moreau.id,
        mother_id=louise_dubois.id,
        marriage=MarriageType.MARRIED,
        notes="Famille François MOREAU - Louise DUBOIS"
    )
    
    session.add(family_pierre)
    session.add(family_paul)
    session.add(family_jeanne)
    session.add(family_louise)
    session.commit()
    
    # ==========================================
    # GÉNÉRATION 3 - COUSINS QUI SE MARIENT
    # ==========================================
    
    birth_1900 = create_test_date(1900)
    birth_1902 = create_test_date(1902)
    birth_1905 = create_test_date(1905)
    birth_1907 = create_test_date(1907)
    birth_1910 = create_test_date(1910)
    birth_1912 = create_test_date(1912)
    
    session.add(birth_1900)
    session.add(birth_1902)
    session.add(birth_1905)
    session.add(birth_1907)
    session.add(birth_1910)
    session.add(birth_1912)
    session.commit()
    
    # Enfants de Pierre et Catherine
    albert_dubois = PersonORM(
        first_name="Albert",
        surname="DUBOIS",
        sex=Sex.MALE,
        parent_family_id=family_pierre.id,
        occupation="Mécanicien",
        notes="Petit-fils des ancêtres communs - fils de Pierre"
    )
    session.add(albert_dubois)
    session.commit()
    
    alice_dubois = PersonORM(
        first_name="Alice",
        surname="DUBOIS",
        sex=Sex.FEMALE,
        parent_family_id=family_pierre.id,
        occupation="Institutrice",
        notes="Petite-fille des ancêtres communs - fille de Pierre"
    )
    session.add(alice_dubois)
    session.commit()
    
    # Enfants de Paul et Marguerite
    robert_dubois = PersonORM(
        first_name="Robert",
        surname="DUBOIS",
        sex=Sex.MALE,
        parent_family_id=family_paul.id,
        occupation="Comptable",
        notes="Petit-fils des ancêtres communs - fils de Paul"
    )
    session.add(robert_dubois)
    session.commit()
    
    # Enfants de Jeanne et Henri
    suzanne_rousseau = PersonORM(
        first_name="Suzanne",
        surname="ROUSSEAU",
        sex=Sex.FEMALE,
        parent_family_id=family_jeanne.id,
        occupation="Secrétaire",
        notes="Petite-fille des ancêtres communs - fille de Jeanne"
    )
    session.add(suzanne_rousseau)
    session.commit()
    
    # Enfants de Louise et François
    michel_moreau = PersonORM(
        first_name="Michel",
        surname="MOREAU",
        sex=Sex.MALE,
        parent_family_id=family_louise.id,
        occupation="Ingénieur",
        notes="Petit-fils des ancêtres communs - fils de Louise"
    )
    session.add(michel_moreau)
    session.commit()
    
    # Événements de naissance pour la génération 3
    albert_birth = EventORM(event_type=EventType.BIRTH, birth_person_id=albert_dubois.id, date_id=birth_1900.id, place_id=lyon.id)
    alice_birth = EventORM(event_type=EventType.BIRTH, birth_person_id=alice_dubois.id, date_id=birth_1902.id, place_id=lyon.id)
    robert_birth = EventORM(event_type=EventType.BIRTH, birth_person_id=robert_dubois.id, date_id=birth_1905.id, place_id=paris.id)
    suzanne_birth = EventORM(event_type=EventType.BIRTH, birth_person_id=suzanne_rousseau.id, date_id=birth_1907.id, place_id=marseille.id)
    michel_birth = EventORM(event_type=EventType.BIRTH, birth_person_id=michel_moreau.id, date_id=birth_1910.id, place_id=marseille.id)
    
    session.add(albert_birth)
    session.add(alice_birth)
    session.add(robert_birth)
    session.add(suzanne_birth)
    session.add(michel_birth)
    session.commit()
    
    # ==========================================
    # MARIAGES CONSANGUINS - GÉNÉRATION 3
    # ==========================================
    
    # Mariage 1 : Albert DUBOIS (fils de Pierre) × Suzanne ROUSSEAU (fille de Jeanne)
    # = Cousins germains (consanguinité 1/16 = 6.25%)
    family_consang_1 = FamilyORM(
        father_id=albert_dubois.id,
        mother_id=suzanne_rousseau.id,
        marriage=MarriageType.MARRIED,
        notes="MARIAGE CONSANGUIN - Cousins germains (Albert fils de Pierre × Suzanne fille de Jeanne)"
    )
    session.add(family_consang_1)
    session.commit()
    
    # Mariage 2 : Robert DUBOIS (fils de Paul) × Alice DUBOIS (fille de Pierre)  
    # = Cousins germains (consanguinité 1/16 = 6.25%)
    family_consang_2 = FamilyORM(
        father_id=robert_dubois.id,
        mother_id=alice_dubois.id,
        marriage=MarriageType.MARRIED,
        notes="MARIAGE CONSANGUIN - Cousins germains (Robert fils de Paul × Alice fille de Pierre)"
    )
    session.add(family_consang_2)
    session.commit()
    
    # ==========================================
    # GÉNÉRATION 4 - ENFANTS CONSANGUINS
    # ==========================================
    
    birth_1925_1 = create_test_date(1925)
    birth_1927 = create_test_date(1927)
    birth_1930 = create_test_date(1930)
    birth_1932 = create_test_date(1932)
    birth_1935 = create_test_date(1935)
    
    session.add(birth_1925_1)
    session.add(birth_1927)
    session.add(birth_1930)
    session.add(birth_1932)
    session.add(birth_1935)
    session.commit()
    
    # Enfants d'Albert et Suzanne (cousins germains)
    jean_albert = PersonORM(
        first_name="Jean",
        surname="DUBOIS",
        sex=Sex.MALE,
        parent_family_id=family_consang_1.id,
        occupation="Employé",
        consang=0.0625,  # 6.25% - parents cousins germains
        notes="CONSANGUINITÉ ÉLEVÉE (6.25%) - Parents cousins germains (Albert × Suzanne)"
    )
    session.add(jean_albert)
    session.commit()
    
    marie_albert = PersonORM(
        first_name="Marie",
        surname="DUBOIS",
        sex=Sex.FEMALE,
        parent_family_id=family_consang_1.id,
        occupation="Employée",
        consang=0.0625,  # 6.25% - parents cousins germains
        notes="CONSANGUINITÉ ÉLEVÉE (6.25%) - Parents cousins germains (Albert × Suzanne)"
    )
    session.add(marie_albert)
    session.commit()
    
    # Enfants de Robert et Alice (cousins germains)
    pierre_robert = PersonORM(
        first_name="Pierre",
        surname="DUBOIS",
        sex=Sex.MALE,
        parent_family_id=family_consang_2.id,
        occupation="Ouvrier",
        consang=0.0625,  # 6.25% - parents cousins germains
        notes="CONSANGUINITÉ ÉLEVÉE (6.25%) - Parents cousins germains (Robert × Alice)"
    )
    session.add(pierre_robert)
    session.commit()
    
    # Événements de naissance pour la génération 4
    jean_albert_birth = EventORM(event_type=EventType.BIRTH, birth_person_id=jean_albert.id, date_id=birth_1925_1.id, place_id=paris.id)
    marie_albert_birth = EventORM(event_type=EventType.BIRTH, birth_person_id=marie_albert.id, date_id=birth_1927.id, place_id=paris.id)
    pierre_robert_birth = EventORM(event_type=EventType.BIRTH, birth_person_id=pierre_robert.id, date_id=birth_1930.id, place_id=lyon.id)
    
    session.add(jean_albert_birth)
    session.add(marie_albert_birth)
    session.add(pierre_robert_birth)
    session.commit()
    
    # ==========================================
    # CONSANGUINITÉ MOYENNE ET FAIBLE
    # ==========================================
    
    # Ajoutons quelques personnes avec consanguinité plus faible pour la variété
    
    # Cousins issus de germains (consanguinité 1/64 = 1.56%)
    cousin_germain_1 = PersonORM(
        first_name="André",
        surname="LEFEBVRE",
        sex=Sex.MALE,
        occupation="Artisan",
        consang=0.0156,  # 1.56% - cousins issus de germains
        notes="CONSANGUINITÉ MOYENNE (1.56%) - Parents cousins issus de germains"
    )
    session.add(cousin_germain_1)
    
    cousin_germain_2 = PersonORM(
        first_name="Berthe",
        surname="LEFEBVRE",
        sex=Sex.FEMALE,
        occupation="Ménagère",
        consang=0.0156,  # 1.56% - cousins issus de germains
        notes="CONSANGUINITÉ MOYENNE (1.56%) - Parents cousins issus de germains"
    )
    session.add(cousin_germain_2)
    
    # Arrière-cousins (consanguinité 1/256 = 0.39%)
    arriere_cousin_1 = PersonORM(
        first_name="Georges",
        surname="DURAND",
        sex=Sex.MALE,
        occupation="Commerçant",
        consang=0.0039,  # 0.39% - arrière-cousins
        notes="CONSANGUINITÉ FAIBLE (0.39%) - Parents arrière-cousins"
    )
    session.add(arriere_cousin_1)
    
    arriere_cousin_2 = PersonORM(
        first_name="Simone",
        surname="DURAND",
        sex=Sex.FEMALE,
        occupation="Vendeuse",
        consang=0.0039,  # 0.39% - arrière-cousins
        notes="CONSANGUINITÉ FAIBLE (0.39%) - Parents arrière-cousins"
    )
    session.add(arriere_cousin_2)
    
    # Personnes avec consanguinité très faible (parenté lointaine)
    parenté_lointaine_1 = PersonORM(
        first_name="Claude",
        surname="LAMBERT",
        sex=Sex.MALE,
        occupation="Professeur",
        consang=0.001,  # 0.1% - parenté très lointaine
        notes="CONSANGUINITÉ TRÈS FAIBLE (0.1%) - Parenté très lointaine"
    )
    session.add(parenté_lointaine_1)
    
    parenté_lointaine_2 = PersonORM(
        first_name="Denise",
        surname="LAMBERT",
        sex=Sex.FEMALE,
        occupation="Infirmière",
        consang=0.001,  # 0.1% - parenté très lointaine
        notes="CONSANGUINITÉ TRÈS FAIBLE (0.1%) - Parenté très lointaine"
    )
    session.add(parenté_lointaine_2)
    
    session.commit()
    
    print("✅ Données de test avec consanguinité ajoutées avec succès !")
    print("\nRésumé des données créées :")
    print("- Génération 1 : Jean DUBOIS × Marie MARTIN (ancêtres communs)")
    print("- Génération 2 : 4 enfants mariés à des non-apparentés")
    print("- Génération 3 : Cousins germains qui se marient entre eux")
    print("- Génération 4 : 3 enfants avec consanguinité élevée (6.25%)")
    print("- Personnes avec consanguinité moyenne (1.56%)")
    print("- Personnes avec consanguinité faible (0.39%)")
    print("- Personnes avec consanguinité très faible (0.1%)")
    print("\nNiveaux de consanguinité créés :")
    print("- Élevée (6.25%) : 3 personnes")
    print("- Moyenne (1.56%) : 2 personnes") 
    print("- Faible (0.39%) : 2 personnes")
    print("- Très faible (0.1%) : 2 personnes")


def main():
    """Fonction principale."""
    
    # Configuration de la base de données
    database_url = "sqlite:///geneweb.db"
    db_manager = DatabaseManager(database_url)
    
    # Créer les tables si nécessaire
    db_manager.create_tables()
    
    # Obtenir une session
    session = db_manager.get_session()
    
    try:
        # Vérifier si des données existent déjà
        existing_persons = session.query(PersonORM).count()
        
        if existing_persons > 0:
            response = input(f"Il y a déjà {existing_persons} personnes dans la base de données. Voulez-vous ajouter les données de test quand même ? (o/n): ")
            if response.lower() not in ['o', 'oui', 'y', 'yes']:
                print("Opération annulée.")
                return
        
        # Ajouter les données de test
        add_consanguineous_family(session)
        
        # Afficher les statistiques finales
        total_persons = session.query(PersonORM).count()
        consanguinous_persons = session.query(PersonORM).filter(PersonORM.consang > 0).count()
        
        print(f"\n📊 Statistiques finales :")
        print(f"- Total des personnes : {total_persons}")
        print(f"- Personnes avec consanguinité : {consanguinous_persons}")
        print(f"- Personnes sans consanguinité : {total_persons - consanguinous_persons}")
        
        if consanguinous_persons > 0:
            avg_consang = session.query(PersonORM.consang).filter(PersonORM.consang > 0).all()
            avg_consang_val = sum(c[0] for c in avg_consang) / len(avg_consang)
            print(f"- Consanguinité moyenne : {avg_consang_val:.4f} ({avg_consang_val * 100:.2f}%)")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout des données : {e}")
        session.rollback()
        
    finally:
        session.close()


if __name__ == "__main__":
    main()