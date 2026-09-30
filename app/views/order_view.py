from fluxfast import Page, resource, scope
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import OrderController


class OrderView:
    """MVC View: Assembles Page descriptors for orders lists and order invoices."""

    @staticmethod
    def render_orders(db: AsyncSession, customer_id: int | None = None) -> Page:
        order_scope = scope.user(customer_id) if customer_id is not None else scope.public()
        return Page(
            component="orders/index",
            resources=[
                resource(
                    "customer-orders",
                    lambda: OrderController.get_orders(db, customer_id=customer_id),
                    scope=order_scope,
                    ttl=15,
                )
            ],
            meta={"title": "Order Management & Tracking"},
        )

    @staticmethod
    def render_detail(db: AsyncSession, order_id: int) -> Page:
        return Page(
            component="orders/detail",
            resources=[
                resource(
                    f"order-detail-{order_id}",
                    lambda: OrderController.get_order(db, order_id),
                    scope=scope.public(),
                    ttl=30,
                )
            ],
            meta={"title": f"Order #{order_id} Invoice"},
        )
