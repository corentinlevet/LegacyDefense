"""
Web UI routes for configuration pages.
"""

import pathlib

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Chemin vers le dossier contenant les templates
templates_path = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

router = APIRouter()


@router.get(
    "/genealogy/{name}/config",
    response_class=HTMLResponse,
    name="genealogy_config_home",
)
async def genealogy_config_home(name: str, request: Request):
    """
    Serves the home page for a specific genealogy's configuration.
    """
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
    name="genealogy_database_config",
)
async def genealogy_database_config(name: str, request: Request):
    """
    Serves the database configuration page for a specific genealogy.
    """
    return templates.TemplateResponse(
        "database_config.html",
        {
            "request": request,
            "genealogy_name": name,
        },
    )


@router.get("/config/server", response_class=HTMLResponse, name="server_config_page")
async def server_config_page(request: Request):
    """
    Serves the global server configuration page.
    """
    return templates.TemplateResponse(
        "server_config.html",
        {
            "request": request,
        },
    )
