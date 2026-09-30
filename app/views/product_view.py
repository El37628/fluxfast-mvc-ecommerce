from fluxfast import Page, resource, scope
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import ProductController


class ProductView:
    """MVC View: Assembles Page descriptors for catalog browsing and product details."""

    @staticmethod
    def render_catalog(
        db: AsyncSession,
        category_id: int | None = None,
        search: str | None = None,
    ) -> Page:
        return Page(
            component="products/index",
            resources=[
                resource(
                    "categories-list",
                    lambda: ProductController.get_categories(db),
                    scope=scope.public(),
                    ttl=300,
                ),
                resource(
                    "product-catalog",
                    lambda: ProductController.get_catalog(db, category_id=category_id, search=search),
                    scope=scope.public(),
                    ttl=30,
                ),
            ],
            meta={"title": "Product Catalog · FluxFast Store"},
        )

    @staticmethod
    def render_detail(db: AsyncSession, product_id: int) -> Page:
        return Page(
            component="products/detail",
            resources=[
                resource(
                    f"product-detail-{product_id}",
                    lambda: ProductController.get_product(db, product_id),
                    scope=scope.public(),
                    ttl=30,
                )
            ],
            meta={"title": f"Product #{product_id} Details"},
        )
