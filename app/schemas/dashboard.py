from pydantic import BaseModel

from .order import OrderSummary
from .product import ProductListItem


class DashboardSummary(BaseModel):
    total_revenue: float
    total_orders: int
    low_stock_count: int
    total_products: int
    pending_orders_count: int
    recent_orders: list[OrderSummary]
    top_products: list[ProductListItem]
