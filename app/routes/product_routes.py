from fastapi import Depends, Query
from fluxfast import FluxRouter, MutationResult, Page
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import ProductController
from app.core.database import get_db
from app.schemas import CreateProductInput, UpdateStockInput
from app.views import ProductView

router = FluxRouter(prefix="/products", tags=["products"])


@router.page("", name="products_catalog")
async def list_products(
    category_id: int | None = Query(None, description="Filter by category ID"),
    search: str | None = Query(None, description="Search by name or SKU"),
    db: AsyncSession = Depends(get_db),
) -> Page:
    """MVC Action: Render product catalog view."""
    return ProductView.render_catalog(db, category_id=category_id, search=search)


@router.page("/{product_id}", name="product_detail")
async def show_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> Page:
    """MVC Action: Render single product view."""
    return ProductView.render_detail(db, product_id=product_id)


@router.mutation("", methods=["POST"], name="create_product")
async def create_product(
    payload: CreateProductInput,
    db: AsyncSession = Depends(get_db),
) -> MutationResult:
    """MVC Action: Invoke controller to create a new product and return mutation patches."""
    return await ProductController.create_product(db, payload)


@router.mutation("/{product_id}/stock", methods=["PATCH"], name="update_product_stock")
async def update_stock(
    product_id: int,
    payload: UpdateStockInput,
    db: AsyncSession = Depends(get_db),
) -> MutationResult:
    """MVC Action: Invoke controller to adjust stock inventory and return mutation patches."""
    return await ProductController.update_stock(db, product_id, payload)
