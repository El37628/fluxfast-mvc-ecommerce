import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_page(client: AsyncClient):
    response = await client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()

    assert data["protocol"] == "fluxfast/1"
    assert data["page"]["component"] == "dashboard/index"
    assert "dashboard-summary" in data["resources"]

    summary = data["resources"]["dashboard-summary"]["value"]
    assert summary["total_orders"] >= 3
    assert summary["total_products"] >= 7
    assert summary["total_revenue"] > 0
    assert len(summary["recent_orders"]) > 0


@pytest.mark.asyncio
async def test_products_page(client: AsyncClient):
    response = await client.get("/products")
    assert response.status_code == 200
    data = response.json()

    assert data["protocol"] == "fluxfast/1"
    assert data["page"]["component"] == "products/index"
    assert "categories-list" in data["resources"]
    assert "product-catalog" in data["resources"]

    products = data["resources"]["product-catalog"]["value"]
    assert len(products) >= 7
    categories = data["resources"]["categories-list"]["value"]
    assert len(categories) >= 4


@pytest.mark.asyncio
async def test_product_detail_page(client: AsyncClient):
    response = await client.get("/products/1")
    assert response.status_code == 200
    data = response.json()

    assert data["protocol"] == "fluxfast/1"
    assert data["page"]["component"] == "products/detail"
    assert "product-detail-1" in data["resources"]

    product = data["resources"]["product-detail-1"]["value"]
    assert product["sku"] == "PROD-MBP"
    assert product["name"] == "MacBook Pro M3 Max"


@pytest.mark.asyncio
async def test_orders_page_with_customer_scope(client: AsyncClient):
    response = await client.get("/orders?customer_id=1")
    assert response.status_code == 200
    data = response.json()

    assert data["protocol"] == "fluxfast/1"
    assert data["page"]["component"] == "orders/index"
    assert "customer-orders" in data["resources"]

    orders = data["resources"]["customer-orders"]["value"]
    assert len(orders) >= 1
    assert all(o["customer_id"] == 1 for o in orders)
