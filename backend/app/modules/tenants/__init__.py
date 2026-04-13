"""Tenants module public entrypoints.

Keep `api.py` as the single API entrypoint for this module.
"""

from app.modules.tenants.api import router

__all__ = ["router"]
