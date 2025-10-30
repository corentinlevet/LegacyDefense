import pathlib
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, logger
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ...application.services import ApplicationService
from ...presentation.dependencies import get_app_service

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
async def view_genealogy(
    name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Sert la page d'accueil pour une généalogie spécifique,
    en récupérant les données via la couche de service.
    """
    details = await app_service.get_genealogy_details(name)
    print(details)
    if not details:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "genealogy_dashboard.html",
        {
            "request": request,
            "genealogy_name": name,
            "nb_persons": details.person_count,
        },
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


@router.get("/genealogy/{genealogy_name}/book/first_names", response_class=HTMLResponse)
async def book_first_names(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Affiche le livre des prénoms pour une généalogie.
    """
    first_names = await app_service.get_first_names(genealogy_name)
    if first_names is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_first_names.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "first_names": first_names,
        },
    )


@router.get("/genealogy/{genealogy_name}/book/last_names", response_class=HTMLResponse)
async def book_last_names(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Affiche le livre des noms pour une généalogie.
    """
    last_names = await app_service.get_last_names(genealogy_name)
    if last_names is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_last_names.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "last_names": last_names,
        },
    )


@router.get("/genealogy/{genealogy_name}/book/places", response_class=HTMLResponse)
async def book_places(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Affiche le livre des lieux pour une généalogie.
    """
    places = await app_service.get_places(genealogy_name)
    if places is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_places.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "places": places,
        },
    )


@router.get("/genealogy/{genealogy_name}/book/occupations", response_class=HTMLResponse)
async def book_occupations(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Affiche le livre des occupations pour une généalogie.
    """
    occupations = await app_service.get_occupations(genealogy_name)
    if occupations is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_occupations.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "occupations": occupations,
        },
    )


@router.get("/genealogy/{genealogy_name}/book/sources", response_class=HTMLResponse)
async def book_sources(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """
    Affiche le livre des sources pour une généalogie.
    """
    sources = await app_service.get_sources(genealogy_name)
    if sources is None:
        raise HTTPException(status_code=404, detail="Genealogy not found")

    return templates.TemplateResponse(
        "book_sources.html",
        {"request": request, "genealogy_name": genealogy_name, "sources": sources},
    )


@router.get("/genealogy/{genealogy_name}/stats", response_class=HTMLResponse)
async def statistics_page(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    """Page des statistiques pour une généalogie"""
    try:
        # Récupère toutes les statistiques
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
    places_hierarchy = await app_service.get_places_surnames(genealogy_name)
    return templates.TemplateResponse(
        "places_surnames.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "places_hierarchy": places_hierarchy,
            "_": gettext,
        },
    )


@router.get(
    "/genealogy/{genealogy_name}/add_family",
    response_class=HTMLResponse,
    name="add_family",
)
async def add_family_form(genealogy_name: str, request: Request):
    return templates.TemplateResponse(
        "add_family.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "_": gettext,
        },
    )


@router.post("/genealogy/{genealogy_name}/add_family", name="add_family_post")
async def add_family_post(
    genealogy_name: str,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    form_data = await request.form()
    family_id = await app_service.add_family(genealogy_name, form_data)
    return RedirectResponse(
        url=f"/genealogy/{genealogy_name}/family/{family_id}", status_code=303
    )


@router.get(
    "/genealogy/{genealogy_name}/family/{family_id}",
    response_class=HTMLResponse,
    name="family_created",
)
async def family_created(
    genealogy_name: str,
    family_id: int,
    request: Request,
    app_service: ApplicationService = Depends(get_app_service),
):
    family = await app_service.get_family(family_id)
    return templates.TemplateResponse(
        "family_created.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "family": family,
            "_": gettext,
        },
    )


from ...presentation.web.formatters import format_date_natural


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
    person = await app_service.get_person_details(person_id)
    return templates.TemplateResponse(
        "person_profile.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "person": person,
            "_": gettext,
            "format_date_natural": format_date_natural,
        },
    )


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


def gettext(text: str) -> str:
    # Ceci est un mock. Remplacez par votre vraie fonction de traduction.
    translations = {
        "Anniversaries": "Anniversaires",
        "Home": "Accueil",
        "Birthdays": "Anniversaires de naissance",
        "Anniversaries of dead people": "Anniversaires de décès",
        "Wedding anniversaries": "Anniversaires de mariage",
    }
    return translations.get(text, text)


@router.get(
    "/genealogy/{genealogy_name}/anniversaries",
    response_class=HTMLResponse,
    name="anniversaries_menu",
)
async def anniversaries_menu(genealogy_name: str, request: Request):
    """
    Affiche le menu principal des anniversaires.
    """
    # Ajout de la fonction de traduction au contexte du template
    return templates.TemplateResponse(
        "anniversaries_menu.html",
        {"request": request, "genealogy_name": genealogy_name, "_": gettext},
    )


@router.get(
    "/genealogy/{genealogy_name}/anniversaries/birth",
    response_class=HTMLResponse,
    name="birth_anniversaries",
)
async def birth_anniversaries(
    genealogy_name: str,
    request: Request,
    month: int = None,
    app_service: ApplicationService = Depends(get_app_service),
):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    today_anniversaries = await app_service.get_birth_anniversaries(
        genealogy_name, target_date=today
    )
    tomorrow_anniversaries = await app_service.get_birth_anniversaries(
        genealogy_name, target_date=tomorrow
    )
    day_after_anniversaries = await app_service.get_birth_anniversaries(
        genealogy_name, target_date=day_after
    )

    month_anniversaries = None
    month_name = None
    if month:
        month_anniversaries = await app_service.get_birth_anniversaries_for_month(
            genealogy_name, month
        )
        month_name = datetime(1900, month, 1).strftime("%B")

    return templates.TemplateResponse(
        "birth_anniversaries.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "today_date": today.strftime("%A %d %B %Y"),
            "tomorrow_date": tomorrow.strftime("%A %d %B %Y"),
            "day_after_date": day_after.strftime("%A %d %B %Y"),
            "today_birthdays": today_anniversaries,
            "tomorrow_birthdays": tomorrow_anniversaries,
            "day_after_birthdays": day_after_anniversaries,
            "month_birthdays": month_anniversaries,
            "selected_month": month,
            "month_name": month_name,
            "_": gettext,
        },
    )


@router.get(
    "/genealogy/{genealogy_name}/anniversaries/death",
    response_class=HTMLResponse,
    name="death_anniversaries",
)
async def death_anniversaries(
    genealogy_name: str,
    request: Request,
    month: int = None,
    app_service: ApplicationService = Depends(get_app_service),
):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    today_anniversaries = await app_service.get_death_anniversaries(
        genealogy_name, target_date=today
    )
    tomorrow_anniversaries = await app_service.get_death_anniversaries(
        genealogy_name, target_date=tomorrow
    )
    day_after_anniversaries = await app_service.get_death_anniversaries(
        genealogy_name, target_date=day_after
    )

    month_anniversaries = None
    month_name = None
    if month:
        month_anniversaries = await app_service.get_death_anniversaries_for_month(
            genealogy_name, month
        )
        month_name = datetime(1900, month, 1).strftime("%B")

    return templates.TemplateResponse(
        "death_anniversaries.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "today_date": today.strftime("%A %d %B %Y"),
            "tomorrow_date": tomorrow.strftime("%A %d %B %Y"),
            "day_after_date": day_after.strftime("%A %d %B %Y"),
            "today_anniversaries": today_anniversaries,
            "tomorrow_anniversaries": tomorrow_anniversaries,
            "day_after_anniversaries": day_after_anniversaries,
            "month_anniversaries": month_anniversaries,
            "selected_month": month,
            "month_name": month_name,
            "_": gettext,
        },
    )


@router.get(
    "/genealogy/{genealogy_name}/anniversaries/marriage",
    response_class=HTMLResponse,
    name="marriage_anniversaries",
)
async def marriage_anniversaries(
    genealogy_name: str,
    request: Request,
    month: int = None,
    app_service: ApplicationService = Depends(get_app_service),
):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    today_anniversaries = await app_service.get_marriage_anniversaries(
        genealogy_name, target_date=today
    )
    tomorrow_anniversaries = await app_service.get_marriage_anniversaries(
        genealogy_name, target_date=tomorrow
    )
    day_after_anniversaries = await app_service.get_marriage_anniversaries(
        genealogy_name, target_date=day_after
    )

    month_anniversaries = None
    month_name = None
    if month:
        month_anniversaries = await app_service.get_marriage_anniversaries_for_month(
            genealogy_name, month
        )
        month_name = datetime(1900, month, 1).strftime("%B")

    return templates.TemplateResponse(
        "marriage_anniversaries.html",
        {
            "request": request,
            "genealogy_name": genealogy_name,
            "today_date": today.strftime("%A %d %B %Y"),
            "tomorrow_date": tomorrow.strftime("%A %d %B %Y"),
            "day_after_date": day_after.strftime("%A %d %B %Y"),
            "today_anniversaries": today_anniversaries,
            "tomorrow_anniversaries": tomorrow_anniversaries,
            "day_after_anniversaries": day_after_anniversaries,
            "month_anniversaries": month_anniversaries,
            "selected_month": month,
            "month_name": month_name,
            "_": gettext,
        },
    )
