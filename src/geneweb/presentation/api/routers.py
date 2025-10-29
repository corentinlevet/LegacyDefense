from fastapi import APIRouter

from .genealogy_api import router as genealogy_api_router

router = APIRouter()

router.include_router(genealogy_api_router)
