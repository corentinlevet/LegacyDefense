"""
Infrastructure Layer - Repositories Package.

This package contains the concrete\
    implementations of the domain's repository interfaces.
"""

from .sql_person_repository import SQLPersonRepository

__all__ = ["SQLPersonRepository"]
