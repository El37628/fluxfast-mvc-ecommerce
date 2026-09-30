import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_product_mutation(client: AsyncClient):
    payload = {
        "sku": "PROD-KEYB",
        "name": "Wireless Mechanical Keyboard",
        "category_id": 1,
        "price": 149.99,
        "stock_quantity": 25,
    }
    response = await client.post("/products", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["protocol"] == "fluxfast/1"
    assert "mutation" in data
    patches = data["mutation"]["patches"]
    assert "product-catalog" in patches
    assert patches["product-catalog"][0]["op"] == "append-item"
    assert patches["product-catalog"][0]["value"]["sku"] == "PROD-KEYB"

    # Verify invalidations
    invalidations = data["mutation"]["invalidate"]
    assert "dashboard-summary" in invalidations
    assert "categories-list" in invalidations


@pytest.mark.asyncio
async def test_update_product_stock_mutation(client: AsyncClient):
    payload = {
        "stock_quantity": 99,
        "change_reason": "Bulk supplier restock",
    }
    response = await client.patch("/products/2/stock", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["protocol"] == "fluxfast/1"
    patches = data["mutation"]["patches"]
    assert "product-catalog" in patches
    assert patches["product-catalog"][0]["op"] == "replace-item"
    assert patches["product-catalog"][0]["value"]["stock_quantity"] == 99


@pytest.mark.asyncio
async def test_checkout_order_mutation(client: AsyncClient):
    payload = {
        "customer_id": 2,
        "items": [
            {"product_id": 3, "quantity": 1},
        ],
        "notes": "Deliver by tomorrow evening",
    }
    response = await client.post("/orders", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["protocol"] == "fluxfast/1"
    patches = data["mutation"]["patches"]
    assert "customer-orders" in patches
    assert patches["customer-orders"][0]["op"] == "append-item"
    assert patches["customer-orders"][0]["value"]["customer_id"] == 2

    # Verify stock was decremented and resources invalidated
    assert "dashboard-summary" in data["mutation"]["invalidate"]
    assert "product-catalog" in data["mutation"]["invalidate"]


@pytest.mark.asyncio
async def test_update_order_status_mutation(client: AsyncClient):
    payload = {"status": "completed"}
    response = await client.patch("/orders/3/status", json=payload)
    assert response.status_code == 200
    data = response.json()

    patches = data["mutation"]["patches"]
    assert "customer-orders" in patches
    assert patches["customer-orders"][0]["op"] == "replace-item"
    assert patches["customer-orders"][0]["value"]["status"] == "completed"
