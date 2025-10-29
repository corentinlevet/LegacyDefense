"""
Routers web pour la configuration GeneWeb.
Ces routes sont ADDITIONNELLES et n'altèrent pas les routes existantes.
"""

import pathlib

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Chemin vers le dossier contenant les templates
templates_path = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

router = APIRouter()


@router.get("/genealogy/{name}/config", response_class=HTMLResponse)
async def genealogy_config_home(name: str, request: Request):
    """Page d'accueil de la configuration d'une généalogie."""
    return templates.TemplateResponse(
        "config_home.html",
        {
            "request": request,
            "genealogy_name": name,
        },
    )


@router.get(
    "/genealogy/{name}/config/database",
    response_class=HTMLResponse,
)
async def genealogy_database_config(name: str, request: Request):
    """Page de configuration de la base de données."""
    return templates.TemplateResponse(
        "database_config.html",
        {
            "request": request,
            "genealogy_name": name,
        },
    )


@router.get("/config/server", response_class=HTMLResponse)
async def server_config_page(request: Request):
    """Page de configuration du serveur."""
    return templates.TemplateResponse(
        "server_config.html",
        {
            "request": request,
        },
    )


@router.get("/admin/errors-stats", response_class=HTMLResponse)
async def errors_stats_page(request: Request):
    """Page d'historique des erreurs et statistiques."""
    return templates.TemplateResponse(
        "errors_stats.html",
        {
            "request": request,
        },
    )
