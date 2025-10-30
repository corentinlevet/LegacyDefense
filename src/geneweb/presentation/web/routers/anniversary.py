"""
Web UI routes for anniversary-related pages.
"""

import pathlib
from datetime import date, datetime, timedelta

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
        "Anniversaries": "Anniversaires",
        "Home": "Accueil",
        "Birthdays": "Anniversaires de naissance",
        "Anniversaries of dead people": "Anniversaires de décès",
        "Wedding anniversaries": "Anniversaires de mariage",
        "Today": "Aujourd'hui",
        "Tomorrow": "Demain",
        "The day after tomorrow": "Après-demain",
        "No birthday today.": "Pas d'anniversaire aujourd'hui.",
        "No birthday tomorrow.": "Pas d'anniversaire demain.",
        "No birthday the day after tomorrow.": "Pas d'anniversaire après-demain.",
        "Select a month to see all the anniversaries.": "Sélectionnez un mois pour voir tous les anniversaires.",
        "January": "Janvier",
        "February": "Février",
        "March": "Mars",
        "April": "Avril",
        "May": "Mai",
        "June": "Juin",
        "July": "Juillet",
        "August": "Août",
        "September": "Septembre",
        "October": "Octobre",
        "November": "Novembre",
        "December": "Décembre",
        "Submit": "Valider",
        "Birthdays in": "Anniversaires en",
        "years": "ans",
        "living": "vivant(e)",
        "No death anniversary today.": "Pas d'anniversaire de décès aujourd'hui.",
        "No death anniversary tomorrow.": "Pas d'anniversaire de décès demain.",
        "No death anniversary the day after tomorrow.": "Pas d'anniversaire de décès après-demain.",
        "Death anniversaries in": "Anniversaires de décès en",
        "No wedding anniversary today.": "Pas d'anniversaire de mariage aujourd'hui.",
        "No wedding anniversary tomorrow.": "Pas d'anniversaire de mariage demain.",
        "No wedding anniversary the day after tomorrow.": "Pas d'anniversaire de mariage après-demain.",
        "Wedding anniversaries in": "Anniversaires de mariage en",
    }
    return translations.get(text, text)


@router.get(
    "/genealogy/{genealogy_name}/anniversaries",
    response_class=HTMLResponse,
    name="anniversaries_menu",
)
async def anniversaries_menu(genealogy_name: str, request: Request):
    """
    Serves the main menu page for anniversaries.
    """
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
    """
    Serves the page displaying birth anniversaries.
    Can filter by month.
    """
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
    """
    Serves the page displaying death anniversaries.
    Can filter by month.
    """
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
    """
    Serves the page displaying marriage anniversaries.
    Can filter by month.
    """
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
