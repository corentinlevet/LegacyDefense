"""
Web UI routes for person-related pages.
"""

import pathlib

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ....application.services import ApplicationService
from ...dependencies import get_app_service
from ..formatters import format_date_natural  # Import the formatter

# Chemin vers le dossier contenant les templates
templates_path = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

router = APIRouter()


@router.get(
    "/genealogy/{genealogy_name}/person/{person_id}",
    response_class=HTMLResponse,
    name="person_profile",
)
async def person_profile(
    genealogy_name: str,
    person_id: int,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Serves the profile page for a specific person within a genealogy.
    """
    person = await app_service.get_person_details(person_id)
    return templates.TemplateResponse(
        "person_profile.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "person": person,
            "_": gettext,  # Assuming gettext is defined or imported globally for templates
            "format_date_natural": format_date_natural,
        },
    )


# Placeholder for gettext function if not imported globally
def gettext(text: str) -> str:
    # This is a mock. Replace with your actual translation function.
    translations = {
        "Basic Info": "Informations de base",
        "Spouse and Children": "Conjoint et Enfants",
        "Genealogy Tree (3 Generations)": "Arbre généalogique (3 générations)",
        "Siblings": "Frères et Sœurs",
        "Born": "Né(e)",
        "in": "à",
        "Died": "Décédé(e)",
        "Occupation": "Profession",
        "on": "le",
        "with": "avec",
        "No siblings found.": "Aucun frère ou sœur trouvé.",
    }
    return translations.get(text, text)
