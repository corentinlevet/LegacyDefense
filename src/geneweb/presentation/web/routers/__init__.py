"""
Main Web UI router for the application.

This router aggregates all web UI sub-routers.
"""

from fastapi import APIRouter

from . import (
    admin,
    anniversary,
    base,
    book,
    config,
    family,
    genealogy,
    person,
    places,
    search,
    stats,
)

router = APIRouter()

router.include_router(admin.router)
router.include_router(anniversary.router)
router.include_router(base.router)
router.include_router(book.router)
router.include_router(config.router)
router.include_router(family.router)
router.include_router(genealogy.router)
router.include_router(person.router)
router.include_router(places.router)
router.include_router(search.router)
router.include_router(stats.router)
