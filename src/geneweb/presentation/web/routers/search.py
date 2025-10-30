"""
Web UI routes for search functionality.
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
        "Search Results": "Résultats de recherche",
        "Search Results for": "Résultats de recherche pour",
        "Back": "Retour",
        "Home": "Accueil",
        "son of": "fils de",
        "daughter of": "fille de",
    }
    return translations.get(text, text)


@router.get(
    "/genealogy/{genealogy_name}/search",
    response_class=HTMLResponse,
    name="search_persons",
)
async def search_persons(
    genealogy_name: str,
    request: Request,
    p: str = None,
    n: str = None,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Serves the search results page for persons within a genealogy.
    Allows searching by first name (p) and surname (n).
    """
    search_query = f"{p or ''} {n or ''}".strip()
    search_results = await app_service.search_persons(genealogy_name, p, n)
    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "search_query": search_query,
            "search_results": search_results,
            "_": gettext,
        },
    )
