from fastapi import Depends, Query
from fluxfast import FluxRouter, MutationResult, Page
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import OrderController
from app.core.database import get_db
from app.schemas import CreateOrderInput, UpdateOrderStatusInput
from app.views import OrderView

router = FluxRouter(prefix="/orders", tags=["orders"])


@router.page("", name="orders_list")
async def list_orders(
    customer_id: int | None = Query(None, description="Filter by customer ID"),
    db: AsyncSession = Depends(get_db),
) -> Page:
    """MVC Action: Render customer orders view."""
    return OrderView.render_orders(db, customer_id=customer_id)


@router.page("/{order_id}", name="order_detail")
async def show_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> Page:
    """MVC Action: Render single order invoice view."""
    return OrderView.render_detail(db, order_id=order_id)


@router.mutation("", methods=["POST"], name="checkout_order")
async def place_order(
    payload: CreateOrderInput,
    db: AsyncSession = Depends(get_db),
) -> MutationResult:
    """MVC Action: Place a new order transactionally and return mutation patches."""
    return await OrderController.create_order(db, payload)


@router.mutation("/{order_id}/status", methods=["PATCH"], name="update_order_status")
async def change_order_status(
    order_id: int,
    payload: UpdateOrderStatusInput,
    db: AsyncSession = Depends(get_db),
) -> MutationResult:
    """MVC Action: Transition order status and return mutation patches."""
    return await OrderController.update_order_status(db, order_id, payload)
