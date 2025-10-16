"""
Template system for GeneWeb Python implementation using Jinja2.

This module provides templating functionality to replace the original
Jingoo template system, with internationalization support.
"""

import gettext
import json
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from .models import Date, Family, Person, Place, Sex


class TemplateEnvironment:
    """Template environment with GeneWeb-specific functions and filters."""

    def __init__(self, template_dir: str = "templates", locale_dir: str = "locales"):
        """Initialize template environment."""
        self.template_dir = template_dir
        self.locale_dir = locale_dir

        # Create template directories if they don't exist
        os.makedirs(template_dir, exist_ok=True)
        os.makedirs(locale_dir, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters and functions
        self._register_filters()
        self._register_globals()

        # Internationalization
        self.current_lang = "en"
        self.translations = {}
        self._load_translations()

    def _register_filters(self):
        """Register custom Jinja2 filters."""

        def date_format(date_obj: Optional[Date], format_type: str = "full") -> str:
            """Format a genealogical date."""
            if not date_obj:
                return ""

            if format_type == "year":
                return str(date_obj.year) if date_obj.year else ""
            elif format_type == "short":
                if date_obj.year and date_obj.month:
                    return f"{date_obj.month:02d}/{date_obj.year}"
                elif date_obj.year:
                    return str(date_obj.year)
                return ""
            else:  # full
                return str(date_obj)

        def place_format(place_obj: Optional[Place], format_type: str = "full") -> str:
            """Format a place."""
            if not place_obj:
                return ""

            if format_type == "short":
                return place_obj.town or place_obj.place or ""
            else:  # full
                return str(place_obj)

        def person_name(person, format_type: str = "full") -> str:
            """Format a person's name."""
            # Handle both dataclass Person and ORM PersonORM objects
            if hasattr(person, "name"):
                # Dataclass Person object
                first_name = person.name.first_name
                surname = person.name.surname
            elif hasattr(person, "first_name"):
                # ORM PersonORM object
                first_name = person.first_name or ""
                surname = person.surname or ""
            else:
                return "Unknown"

            if format_type == "surname_first":
                return f"{surname}, {first_name}".strip(", ")
            elif format_type == "surname":
                return surname
            elif format_type == "first_name":
                return first_name
            else:  # full
                return f"{first_name} {surname}".strip()

        def sex_symbol(sex) -> str:
            """Get symbol for sex."""
            # Handle both Sex enum and string values
            if hasattr(sex, "value"):
                sex_value = sex.value.upper()
            elif isinstance(sex, str):
                sex_value = sex.upper()
            else:
                return "?"

            if sex_value == "MALE":
                return "♂"
            elif sex_value == "FEMALE":
                return "♀"
            else:
                return "?"

        def age_at_death(person: Person) -> Optional[int]:
            """Calculate age at death."""
            if not person.birth or not person.death:
                return None

            birth_date = person.birth.date
            death_date = person.death.date

            if (
                not birth_date
                or not death_date
                or not birth_date.year
                or not death_date.year
            ):
                return None

            age = death_date.year - birth_date.year

            # Adjust for month/day if available
            if (
                birth_date.month
                and death_date.month
                and birth_date.month > death_date.month
            ):
                age -= 1
            elif (
                birth_date.month
                and death_date.month
                and birth_date.month == death_date.month
                and birth_date.day
                and death_date.day
                and birth_date.day > death_date.day
            ):
                age -= 1

            return age

        def living_person(person) -> bool:
            """Check if person is likely still living."""
            # Handle both dataclass Person and PersonORM objects
            if hasattr(person, "death_event"):
                # PersonORM - check death_event relationship (now 1-to-1)
                if person.death_event:
                    return False
            elif hasattr(person, "death"):
                # Person dataclass - check death attribute
                if person.death:
                    return False

            # Check birth date to estimate if person could still be living
            birth_year = None
            if hasattr(person, "birth_event"):
                # PersonORM - get birth year from event (now single object)
                birth_event = person.birth_event
                if (
                    birth_event
                    and hasattr(birth_event, "date")
                    and birth_event.date
                    and birth_event.date.year
                ):
                    birth_year = birth_event.date.year
            elif hasattr(person, "birth") and person.birth:
                # Person dataclass - get birth year from event
                if person.birth.date and person.birth.date.year:
                    birth_year = person.birth.date.year

            if birth_year:
                current_year = datetime.now().year
                age = current_year - birth_year
                return age <= 120  # Reasonable assumption

            return True  # Unknown, assume living

        # Register filters in environment
        self.env.filters["date_format"] = date_format
        self.env.filters["place_format"] = place_format
        self.env.filters["person_name"] = person_name
        self.env.filters["sex_symbol"] = sex_symbol
        self.env.filters["age_at_death"] = age_at_death
        self.env.filters["living_person"] = living_person

        def format_list(
            items: List[Any], separator: str = ", ", last_separator: str = " and "
        ) -> str:
            """Format a list with proper separators."""
            if not items:
                return ""
            if len(items) == 1:
                return str(items[0])
            if len(items) == 2:
                return f"{items[0]}{last_separator}{items[1]}"

            return (
                separator.join(str(item) for item in items[:-1])
                + last_separator
                + str(items[-1])
            )

        # Register the format_list filter
        self.env.filters["format_list"] = format_list

    def _register_globals(self):
        """Register global functions available in templates."""

        def translate(key: str, **kwargs) -> str:
            """Translate a key to current language."""
            translation = self.translations.get(self.current_lang, {}).get(key, key)

            # Simple variable substitution
            for k, v in kwargs.items():
                translation = translation.replace(f"{{{k}}}", str(v))

            return translation

        def url_for(endpoint: str, **kwargs) -> str:
            """Generate URL for endpoint (simplified)."""
            # In a real implementation, this would integrate with the web framework
            base_urls = {
                "person_detail": "/persons/{id}",
                "family_detail": "/families/{id}",
                "search": "/search",
                "home": "/",
                "statistics": "/statistics",
            }

            url = base_urls.get(endpoint, f"/{endpoint}")

            # Simple parameter substitution
            for key, value in kwargs.items():
                url = url.replace(f"{{{key}}}", str(value))

            return url

        def current_year() -> int:
            """Get current year."""
            return datetime.now().year

        def format_number(number: int) -> str:
            """Format number with thousands separators."""
            return f"{number:,}"

        # Register globals
        self.env.globals.update(
            {
                "_": translate,
                "url_for": url_for,
                "current_year": current_year,
                "format_number": format_number,
            }
        )

    def _load_translations(self):
        """Load translation files."""
        for lang_file in os.listdir(self.locale_dir):
            if lang_file.endswith(".json"):
                lang_code = lang_file[:-5]  # Remove .json extension
                try:
                    with open(
                        os.path.join(self.locale_dir, lang_file), "r", encoding="utf-8"
                    ) as f:
                        self.translations[lang_code] = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

    def set_language(self, lang_code: str):
        """Set current language."""
        self.current_lang = lang_code

    def render_template(self, template_name: str, **context) -> str:
        """Render a template with context."""
        template = self.env.get_template(template_name)

        # Add common context variables
        context.update(
            {
                "current_lang": self.current_lang,
                "available_langs": list(self.translations.keys()),
                "now": datetime.now(),
            }
        )

        return template.render(**context)

    def render_string(self, template_string: str, **context) -> str:
        """Render a template string with context."""
        template = self.env.from_string(template_string)

        # Add common context variables
        context.update(
            {
                "current_lang": self.current_lang,
                "available_langs": list(self.translations.keys()),
                "now": datetime.now(),
            }
        )

        return template.render(**context)


# Create default templates
DEFAULT_TEMPLATES = {
    "person_detail.html": """
<!DOCTYPE html>
<html lang="{{ current_lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ person|person_name }} - {{ _('genealogy') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .person-header { border-bottom: 2px solid #ccc; padding-bottom: 10px; margin-bottom: 20px; }
        .person-name { font-size: 2em; font-weight: bold; }
        .person-dates { color: #666; margin-top: 5px; }
        .section { margin-bottom: 30px; }
        .section h3 { color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        .family-link { color: #0066cc; text-decoration: none; }
        .family-link:hover { text-decoration: underline; }
        .sex-symbol { font-size: 1.2em; }
        .living { color: green; }
        .deceased { color: #666; }
    </style>
</head>
<body>
    <div class="person-header">
        <div class="person-name">
            {{ person|person_name }}
            <span class="sex-symbol">{{ person.sex|sex_symbol }}</span>
        </div>
        <div class="person-dates">
            {% if person.birth %}
                {{ _('born') }}: {{ person.birth.date|date_format }}
                {% if person.birth.place %}
                    {{ _('in') }} {{ person.birth.place|place_format }}
                {% endif %}
            {% endif %}
            
            {% if person.death %}
                <br>{{ _('died') }}: {{ person.death.date|date_format }}
                {% if person.death.place %}
                    {{ _('in') }} {{ person.death.place|place_format }}
                {% endif %}
                {% if person|age_at_death %}
                    ({{ _('age') }} {{ person|age_at_death }})
                {% endif %}
            {% elif person|living_person %}
                <br><span class="living">{{ _('living') }}</span>
            {% endif %}
        </div>
    </div>

    {% if person.occupation %}
    <div class="section">
        <h3>{{ _('occupation') }}</h3>
        <p>{{ person.occupation }}</p>
    </div>
    {% endif %}

    {% if parents %}
    <div class="section">
        <h3>{{ _('parents') }}</h3>
        <ul>
            {% if parents.father %}
            <li>{{ _('father') }}: <a href="{{ url_for('person_detail', id=parents.father.id) }}" class="family-link">{{ parents.father|person_name }}</a></li>
            {% endif %}
            {% if parents.mother %}
            <li>{{ _('mother') }}: <a href="{{ url_for('person_detail', id=parents.mother.id) }}" class="family-link">{{ parents.mother|person_name }}</a></li>
            {% endif %}
        </ul>
    </div>
    {% endif %}

    {% if spouses %}
    <div class="section">
        <h3>{{ _('spouses') }}</h3>
        {% for spouse_info in spouses %}
        <div>
            <a href="{{ url_for('person_detail', id=spouse_info.spouse.id) }}" class="family-link">{{ spouse_info.spouse|person_name }}</a>
            {% if spouse_info.marriage_date %}
                ({{ _('married') }} {{ spouse_info.marriage_date|date_format }})
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if children %}
    <div class="section">
        <h3>{{ _('children') }}</h3>
        <ul>
            {% for child in children %}
            <li><a href="{{ url_for('person_detail', id=child.id) }}" class="family-link">{{ child|person_name }}</a></li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    {% if person.notes %}
    <div class="section">
        <h3>{{ _('notes') }}</h3>
        <p>{{ person.notes }}</p>
    </div>
    {% endif %}

    <div class="section">
        <h3>{{ _('actions') }}</h3>
        <ul>
            <li><a href="{{ url_for('person_detail', id=person.id) }}/ancestors" class="family-link">{{ _('view_ancestors') }}</a></li>
            <li><a href="{{ url_for('person_detail', id=person.id) }}/descendants" class="family-link">{{ _('view_descendants') }}</a></li>
            <li><a href="{{ url_for('search') }}" class="family-link">{{ _('search') }}</a></li>
            <li><a href="{{ url_for('home') }}" class="family-link">{{ _('home') }}</a></li>
        </ul>
    </div>
</body>
</html>
    """,
    "family_list.html": """
<!DOCTYPE html>
<html lang="{{ current_lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ _('families') }} - {{ _('genealogy') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .family-card { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .family-parents { font-weight: bold; margin-bottom: 10px; }
        .family-children { margin-top: 10px; }
        .person-link { color: #0066cc; text-decoration: none; }
        .person-link:hover { text-decoration: underline; }
        .marriage-info { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>{{ _('families') }} ({{ families|length }})</h1>
    
    {% for family in families %}
    <div class="family-card">
        <div class="family-parents">
            {% if family.father %}
                <a href="{{ url_for('person_detail', id=family.father.id) }}" class="person-link">{{ family.father|person_name }}</a>
            {% else %}
                {{ _('unknown_father') }}
            {% endif %}
            
            {% if family.mother %}
                &amp; <a href="{{ url_for('person_detail', id=family.mother.id) }}" class="person-link">{{ family.mother|person_name }}</a>
            {% else %}
                &amp; {{ _('unknown_mother') }}
            {% endif %}
        </div>
        
        {% if family.marriage_date %}
        <div class="marriage-info">
            {{ _('married') }}: {{ family.marriage_date|date_format }}
            {% if family.marriage_place %}
                {{ _('in') }} {{ family.marriage_place|place_format }}
            {% endif %}
        </div>
        {% endif %}
        
        {% if family.children %}
        <div class="family-children">
            <strong>{{ _('children') }}:</strong>
            {{ family.children|map('person_name')|format_list }}
        </div>
        {% endif %}
    </div>
    {% endfor %}
    
    {% if not families %}
    <p>{{ _('no_families_found') }}</p>
    {% endif %}
</body>
</html>
    """,
    "search.html": """
<!DOCTYPE html>
<html lang="{{ current_lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ _('search') }} - {{ _('genealogy') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .search-form { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .search-input { width: 300px; padding: 8px; margin-right: 10px; }
        .search-button { padding: 8px 15px; background: #0066cc; color: white; border: none; border-radius: 3px; cursor: pointer; }
        .search-button:hover { background: #0052a3; }
        .result-item { margin: 10px 0; padding: 10px; border-left: 3px solid #0066cc; background: #f9f9f9; }
        .person-link { color: #0066cc; text-decoration: none; font-weight: bold; }
        .person-link:hover { text-decoration: underline; }
        .person-details { color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>{{ _('search_genealogy') }}</h1>
    
    <div class="search-form">
        <form method="GET" action="{{ url_for('search') }}">
            <input type="text" name="q" value="{{ query or '' }}" placeholder="{{ _('enter_name_to_search') }}" class="search-input" required>
            <button type="submit" class="search-button">{{ _('search') }}</button>
        </form>
    </div>
    
    {% if query %}
    <h2>{{ _('search_results_for') }} "{{ query }}" ({{ results|length }} {{ _('found') }})</h2>
    
    {% for person in results %}
    <div class="result-item">
        <div>
            <a href="{{ url_for('person_detail', id=person.id) }}" class="person-link">{{ person|person_name }}</a>
            <span class="sex-symbol">{{ person.sex|sex_symbol }}</span>
        </div>
        <div class="person-details">
            {% if person.birth %}
                {{ _('born') }}: {{ person.birth.date|date_format('year') }}
                {% if person.birth.place %}
                    {{ _('in') }} {{ person.birth.place|place_format('short') }}
                {% endif %}
            {% endif %}
            
            {% if person.death %}
                | {{ _('died') }}: {{ person.death.date|date_format('year') }}
            {% elif person|living_person %}
                | <span class="living">{{ _('living') }}</span>
            {% endif %}
            
            {% if person.occupation %}
                | {{ person.occupation }}
            {% endif %}
        </div>
    </div>
    {% endfor %}
    
    {% if not results %}
    <p>{{ _('no_results_found') }}</p>
    {% endif %}
    {% endif %}
</body>
</html>
    """,
}

# Default translations
DEFAULT_TRANSLATIONS = {
    "en": {
        "genealogy": "Genealogy",
        "born": "Born",
        "died": "Died",
        "in": "in",
        "age": "age",
        "living": "Living",
        "occupation": "Occupation",
        "parents": "Parents",
        "father": "Father",
        "mother": "Mother",
        "spouses": "Spouses",
        "married": "Married",
        "children": "Children",
        "notes": "Notes",
        "actions": "Actions",
        "view_ancestors": "View Ancestors",
        "view_descendants": "View Descendants",
        "search": "Search",
        "home": "Home",
        "families": "Families",
        "unknown_father": "Unknown Father",
        "unknown_mother": "Unknown Mother",
        "no_families_found": "No families found",
        "search_genealogy": "Search Genealogy",
        "enter_name_to_search": "Enter name to search",
        "search_results_for": "Search results for",
        "found": "found",
        "no_results_found": "No results found",
    },
    "fr": {
        "genealogy": "Généalogie",
        "born": "Né(e)",
        "died": "Décédé(e)",
        "in": "à",
        "age": "âge",
        "living": "Vivant(e)",
        "occupation": "Profession",
        "parents": "Parents",
        "father": "Père",
        "mother": "Mère",
        "spouses": "Conjoints",
        "married": "Marié(e)",
        "children": "Enfants",
        "notes": "Notes",
        "actions": "Actions",
        "view_ancestors": "Voir les Ancêtres",
        "view_descendants": "Voir les Descendants",
        "search": "Rechercher",
        "home": "Accueil",
        "families": "Familles",
        "unknown_father": "Père Inconnu",
        "unknown_mother": "Mère Inconnue",
        "no_families_found": "Aucune famille trouvée",
        "search_genealogy": "Recherche Généalogique",
        "enter_name_to_search": "Entrez un nom à rechercher",
        "search_results_for": "Résultats de recherche pour",
        "found": "trouvé(s)",
        "no_results_found": "Aucun résultat trouvé",
    },
}


def initialize_templates(template_dir: str = "templates", locale_dir: str = "locales"):
    """Initialize template system with default templates and translations."""

    # Create directories
    os.makedirs(template_dir, exist_ok=True)
    os.makedirs(locale_dir, exist_ok=True)

    # Create default template files
    for template_name, template_content in DEFAULT_TEMPLATES.items():
        template_path = os.path.join(template_dir, template_name)
        if not os.path.exists(template_path):
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content.strip())

    # Create default translation files
    for lang_code, translations in DEFAULT_TRANSLATIONS.items():
        trans_path = os.path.join(locale_dir, f"{lang_code}.json")
        if not os.path.exists(trans_path):
            with open(trans_path, "w", encoding="utf-8") as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)

    return TemplateEnvironment(template_dir, locale_dir)
