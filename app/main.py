from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fluxfast import FluxFast

from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.seed import seed_data
from app.routes import dashboard_router, order_router, product_router
from app.schemas import (
    CategoryItem,
    DashboardSummary,
    OrderSummary,
    ProductListItem,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing database table creation and seed data."""
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_data(session)
    yield


app = FastAPI(
    title=settings.NAME,
    description="Showcasing how to structure FluxFast with the classic Model-View-Controller (MVC) architecture",
    version="1.0.0",
    lifespan=lifespan,
)

# Initialize FluxFast runtime
flux = FluxFast(app, debug=settings.is_debug)

# Register authoritative typed resource contracts for frontend codegen and type safety
DASHBOARD_SUMMARY = flux.define_resource("dashboard-summary", DashboardSummary)
PRODUCT_CATALOG = flux.define_resource("product-catalog", list[ProductListItem])
CATEGORIES_LIST = flux.define_resource("categories-list", list[CategoryItem])
CUSTOMER_ORDERS = flux.define_resource("customer-orders", list[OrderSummary])

# Mount MVC FluxRouters
app.include_router(dashboard_router)
app.include_router(product_router)
app.include_router(order_router)
