from fluxfast import Page, resource, scope
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import DashboardController


class DashboardView:
    """MVC View: Assembles Page and Resource descriptors for Dashboard presentation."""

    @staticmethod
    def render(db: AsyncSession) -> Page:
        return Page(
            component="dashboard/index",
            resources=[
                resource(
                    "dashboard-summary",
                    lambda: DashboardController.get_summary(db),
                    scope=scope.public(),
                    ttl=15,
                ),
            ],
            meta={"title": "E-Commerce Executive Dashboard"},
        )
