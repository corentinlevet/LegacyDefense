"""
Web UI routes for places and surnames pages.
"""

import pathlib

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ....application.services import ApplicationService
from ...dependencies import get_app_service

# Chemin vers le dossier contenant les templates
templates_path = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

router = APIRouter()


# Placeholder for gettext function if not imported globally
def gettext(text: str) -> str:
    # This is a mock. Replace with your actual translation function.
    translations = {
        "Places / Surnames": "Lieux / Noms",
        "Back": "Retour",
        "Home": "Accueil",
    }
    return translations.get(text, text)


@router.get(
    "/genealogy/{genealogy_name}/places-surnames",
    response_class=HTMLResponse,
    name="places_surnames",
)
async def places_surnames(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Serves the page displaying a hierarchy of places and associated surnames within a genealogy.
    """
    places_surnames_data = await app_service.get_places_surnames(genealogy_name)
    return templates.TemplateResponse(
        "places_surnames.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "places_hierarchy": places_surnames_data,
            "_": gettext,
        },
    )
