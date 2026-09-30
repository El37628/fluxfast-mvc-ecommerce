from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, Order, Product
from app.schemas import DashboardSummary, OrderSummary, ProductListItem


class DashboardController:
    """Controller orchestrating high-level metrics and business KPI aggregation."""

    @staticmethod
    async def get_summary(db: AsyncSession) -> DashboardSummary:
        # Total revenue across non-cancelled orders
        rev_query = select(func.coalesce(func.sum(Order.total_amount), 0.0)).where(
            Order.status != "cancelled"
        )
        rev_res = await db.execute(rev_query)
        total_revenue = float(rev_res.scalar_one())

        # Total order counts
        orders_cnt_res = await db.execute(select(func.count(Order.id)))
        total_orders = int(orders_cnt_res.scalar_one())

        # Pending orders
        pending_cnt_res = await db.execute(
            select(func.count(Order.id)).where(Order.status == "pending")
        )
        pending_orders = int(pending_cnt_res.scalar_one())

        # Low stock products (stock < 10)
        low_stock_res = await db.execute(
            select(func.count(Product.id)).where(Product.stock_quantity < 10)
        )
        low_stock_count = int(low_stock_res.scalar_one())

        # Total products count
        prod_cnt_res = await db.execute(select(func.count(Product.id)))
        total_products = int(prod_cnt_res.scalar_one())

        # Recent 5 orders
        recent_orders_stmt = (
            select(Order)
            .options(selectinload(Order.customer), selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(5)
        )
        recent_orders_res = await db.execute(recent_orders_stmt)
        recent_orders = [
            OrderSummary(
                id=o.id,
                order_number=o.order_number,
                customer_id=o.customer_id,
                customer_name=o.customer.name if o.customer else "Unknown",
                status=o.status,
                total_amount=o.total_amount,
                item_count=len(o.items),
                created_at=o.created_at.isoformat(),
            )
            for o in recent_orders_res.scalars().all()
        ]

        # Top 5 products
        top_prods_stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .order_by(Product.stock_quantity.desc())
            .limit(5)
        )
        top_prods_res = await db.execute(top_prods_stmt)
        top_products = [
            ProductListItem(
                id=p.id,
                sku=p.sku,
                name=p.name,
                category_id=p.category_id,
                category_name=p.category.name if p.category else "Unassigned",
                price=p.price,
                stock_quantity=p.stock_quantity,
                is_active=p.is_active,
            )
            for p in top_prods_res.scalars().all()
        ]

        return DashboardSummary(
            total_revenue=total_revenue,
            total_orders=total_orders,
            low_stock_count=low_stock_count,
            total_products=total_products,
            pending_orders_count=pending_orders,
            recent_orders=recent_orders,
            top_products=top_products,
        )
