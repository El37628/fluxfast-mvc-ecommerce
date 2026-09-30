from fastapi import Depends
from fluxfast import FluxRouter, Page
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.views import DashboardView

router = FluxRouter()


@router.page("/", name="home_dashboard")
@router.page("/dashboard", name="dashboard")
async def show_dashboard(db: AsyncSession = Depends(get_db)) -> Page:
    """MVC Action: Render dashboard view."""
    return DashboardView.render(db)
