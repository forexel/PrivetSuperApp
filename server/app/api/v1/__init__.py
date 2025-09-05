# app/api/v1/__init__.py
from fastapi import APIRouter

from .auth import router as auth_router
from .tickets import router as tickets_router
from .devices import router as devices_router
from .admin import router as admin_router
from .me import router as me_router
from .subscriptions import router as subscriptions_router
from .support import router as support_router
from .ping import router as ping_router
from .users import router as users_router, auth_router as users_auth_router
from .misc import router as misc_router

api_router = APIRouter()
api_router.include_router(ping_router)           # /ping
# api_router.include_router(auth_router)           # /auth
api_router.include_router(users_auth_router) 
api_router.include_router(misc_router)            # /misc
api_router.include_router(me_router)             # /me
api_router.include_router(devices_router)        # /devices
api_router.include_router(tickets_router)        # /tickets
api_router.include_router(subscriptions_router)  # /subscriptions
api_router.include_router(admin_router)          # /admin
api_router.include_router(support_router)  # /support
api_router.include_router(users_router)    
