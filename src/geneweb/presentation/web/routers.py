import pathlib

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Chemin vers le dossier contenant les templates
# On part du principe que ce fichier est dans src/geneweb/presentation/web/
templates_path = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# Création d'un nouveau routeur pour les pages web
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_start_page(request: Request):
    """
    Sert la page d'accueil de l'application.
    """
    context = {"request": request}
    return templates.TemplateResponse("start.html", context)


@router.get("/gwd", response_class=HTMLResponse)
async def read_select_page(request: Request):
    """
    Sert la page de sélection de l'arbre généalogique.
    """
    context = {"request": request}
    return templates.TemplateResponse("gwd.html", context)


@router.get("/gwsetup", response_class=HTMLResponse)
async def read_admin_page(request: Request):
    """
    Sert la page de gestion et de création.
    """
    context = {"request": request}
    return templates.TemplateResponse("gwsetup.html", context)


@router.get("/genealogies/create", response_class=HTMLResponse)
async def create_genealogy_form(request: Request):
    return templates.TemplateResponse("create_genealogy.html", {"request": request})


@router.get("/genealogies", response_class=HTMLResponse)
async def list_genealogies_page(request: Request):
    return templates.TemplateResponse("list_genealogies.html", {"request": request})


@router.get("/genealogy/{name}", response_class=HTMLResponse)
async def view_genealogy(name: str, request: Request):
    return HTMLResponse(
        f"<h1>Viewing Genealogy: {name}</h1><p>Details for {name} would go here.</p>"
    )


@router.get("/genealogies/{genealogy_name}/import", response_class=HTMLResponse)
async def import_gedcom_page(genealogy_name: str, request: Request):
    return templates.TemplateResponse(
        "import_gedcom.html", {"request": request, "genealogy_name": genealogy_name}
    )


@router.get("/genealogies/{genealogy_name}/export", response_class=HTMLResponse)
async def export_gedcom_page(genealogy_name: str, request: Request):
    return templates.TemplateResponse(
        "export_gedcom.html", {"request": request, "genealogy_name": genealogy_name}
    )
