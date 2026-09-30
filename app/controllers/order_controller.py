import uuid
from fastapi import HTTPException
from fluxfast import (
    MutationResult,
    append_item,
    invalidate_resource,
    mutation,
    replace_item,
    scope,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Customer, Order, OrderItem, Product
from app.schemas import (
    CreateOrderInput,
    OrderDetail,
    OrderItemDetail,
    OrderSummary,
    UpdateOrderStatusInput,
)


class OrderController:
    """Controller orchestrating checkout transactions, inventory deductions, and order lifecycle."""

    @staticmethod
    async def get_orders(
        db: AsyncSession,
        customer_id: int | None = None,
    ) -> list[OrderSummary]:
        stmt = select(Order).options(selectinload(Order.customer), selectinload(Order.items))
        if customer_id is not None:
            stmt = stmt.where(Order.customer_id == customer_id)
        stmt = stmt.order_by(Order.created_at.desc())
        res = await db.execute(stmt)
        return [
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
            for o in res.scalars().all()
        ]

    @staticmethod
    async def get_order(db: AsyncSession, order_id: int) -> OrderDetail:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.items).joinedload(OrderItem.product),
            )
            .where(Order.id == order_id)
        )
        res = await db.execute(stmt)
        order = res.scalars().first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        items_detail = [
            OrderItemDetail(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "Deleted Product",
                product_sku=item.product.sku if item.product else "N/A",
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in order.items
        ]

        return OrderDetail(
            id=order.id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            customer_name=order.customer.name if order.customer else "Unknown",
            customer_email=order.customer.email if order.customer else "N/A",
            status=order.status,
            total_amount=order.total_amount,
            notes=order.notes,
            created_at=order.created_at.isoformat(),
            items=items_detail,
        )

    @staticmethod
    async def create_order(
        db: AsyncSession,
        payload: CreateOrderInput,
    ) -> MutationResult:
        # Validate customer
        cust_res = await db.execute(select(Customer).where(Customer.id == payload.customer_id))
        customer = cust_res.scalars().first()
        if not customer:
            raise HTTPException(status_code=400, detail="Customer not found")

        total_amount = 0.0
        order_items_to_create = []

        # Validate products and stock
        for item_in in payload.items:
            prod_res = await db.execute(
                select(Product).where(Product.id == item_in.product_id)
            )
            product = prod_res.scalars().first()
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product ID {item_in.product_id} is unavailable",
                )
            if product.stock_quantity < item_in.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for '{product.name}' (available: {product.stock_quantity}, requested: {item_in.quantity})",
                )

            # Deduct stock
            product.stock_quantity -= item_in.quantity
            line_subtotal = round(product.price * item_in.quantity, 2)
            total_amount += line_subtotal

            order_items_to_create.append(
                OrderItem(
                    product_id=product.id,
                    quantity=item_in.quantity,
                    unit_price=product.price,
                    subtotal=line_subtotal,
                )
            )

        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        new_order = Order(
            customer_id=customer.id,
            order_number=order_number,
            status="pending",
            total_amount=round(total_amount, 2),
            notes=payload.notes,
            items=order_items_to_create,
        )
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)

        order_summary = OrderSummary(
            id=new_order.id,
            order_number=new_order.order_number,
            customer_id=customer.id,
            customer_name=customer.name,
            status=new_order.status,
            total_amount=new_order.total_amount,
            item_count=len(order_items_to_create),
            created_at=new_order.created_at.isoformat(),
        )

        return mutation(
            patches={
                "customer-orders": [append_item(order_summary.model_dump(mode="json"))]
            },
            invalidates=[
                invalidate_resource("dashboard-summary", scope=scope.public()),
                invalidate_resource("product-catalog", scope=scope.public()),
                invalidate_resource("customer-orders", scope=scope.user(customer.id)),
            ],
        )

    @staticmethod
    async def update_order_status(
        db: AsyncSession,
        order_id: int,
        payload: UpdateOrderStatusInput,
    ) -> MutationResult:
        stmt = (
            select(Order)
            .options(selectinload(Order.customer), selectinload(Order.items))
            .where(Order.id == order_id)
        )
        res = await db.execute(stmt)
        order = res.scalars().first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        order.status = payload.status
        await db.commit()
        await db.refresh(order)

        summary = OrderSummary(
            id=order.id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            customer_name=order.customer.name if order.customer else "Unknown",
            status=order.status,
            total_amount=order.total_amount,
            item_count=len(order.items),
            created_at=order.created_at.isoformat(),
        )

        return mutation(
            patches={
                "customer-orders": [replace_item(order.id, summary.model_dump(mode="json"))]
            },
            invalidates=[
                invalidate_resource("dashboard-summary", scope=scope.public()),
                invalidate_resource(f"order-detail-{order.id}", scope=scope.public()),
                invalidate_resource("customer-orders", scope=scope.user(order.customer_id)),
            ],
        )
