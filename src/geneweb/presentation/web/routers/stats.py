"""
Web UI routes for genealogy statistics pages.
"""

import pathlib

from fastapi import APIRouter, Depends, Request, logger
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ....application.services import ApplicationService
from ...dependencies import get_app_service

# Chemin vers le dossier contenant les templates
templates_path = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

router = APIRouter()


@router.get(
    "/genealogy/{genealogy_name}/stats",
    response_class=HTMLResponse,
    name="statistics_page",
)
async def statistics_page(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Serves the statistics page for a specific genealogy.
    Retrieves various statistics like last births, deaths, marriages, oldest couples, etc.
    """
    try:
        last_births = await app_service.get_last_births(genealogy_name)
        last_deaths = await app_service.get_last_deaths(genealogy_name)
        last_marriages = await app_service.get_last_marriages(genealogy_name)
        oldest_couples = await app_service.get_oldest_couples(genealogy_name)
        oldest_alive = await app_service.get_oldest_alive(genealogy_name)
        longest_lived = await app_service.get_longest_lived(genealogy_name)

        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "genealogy_name": genealogy_name,
                "last_births": last_births or [],
                "last_deaths": last_deaths or [],
                "last_marriages": last_marriages or [],
                "oldest_couples": oldest_couples or [],
                "oldest_alive": oldest_alive or [],
                "longest_lived": longest_lived or [],
            },
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "genealogy_name": genealogy_name,
                "error": "Impossible de charger les statistiques",
            },
        )
