from .dashboard_routes import router as dashboard_router
from .order_routes import router as order_router
from .product_routes import router as product_router

__all__ = [
    "dashboard_router",
    "product_router",
    "order_router",
]
