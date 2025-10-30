"""
Main API router for the application.

This router aggregates all API sub-routers.
"""

from fastapi import APIRouter

from . import genealogy_api, server_api

api_router = APIRouter(prefix="/api")

api_router.include_router(genealogy_api.router, prefix="/genealogies")
api_router.include_router(server_api.router, prefix="/server")
