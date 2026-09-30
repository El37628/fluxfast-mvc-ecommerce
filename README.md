# FluxFast MVC E-Commerce Showcase

A production-grade reference implementation demonstrating how to structure a **FluxFast** application using the classic **Model-View-Controller (MVC)** architectural pattern with **FastAPI** and **MySQL**.

---

## Architecture Overview

In traditional MVC web frameworks (like Ruby on Rails, Django, or ASP.NET MVC), the **Model** owns the data and persistence rules, the **Controller** processes user inputs and business transactions, and the **View** renders the user-facing response.

In a **FluxFast + FastAPI** application:
- **Models (`app/models/`)**: SQLAlchemy 2.0 async ORM models representing relational tables (`Category`, `Customer`, `Product`, `Order`, `OrderItem`).
- **Views (`app/views/`)**: Server-driven UI page builders. In FluxFast, Views instantiate `Page(component="...", resources=[...], meta={...})`. Views declare what frontend component should render, define resource loaders, and configure caching scopes (`scope.public()`, `scope.user(...)`) and TTLs.
- **Controllers (`app/controllers/`)**: Business logic and orchestrators. Controllers query data for views, execute transactional workflows (such as inventory deduction during checkout), and construct `MutationResult` payloads with atomic patches (`append_item`, `replace_item`) and scoped cache invalidations (`invalidate_resource`).
- **Routes (`app/routes/`)**: Web delivery layer using `FluxRouter()`. Maps HTTP requests and FluxFast protocol calls (`X-FluxFast: 1`) to View renders (`@router.page`) and Controller actions (`@router.mutation`).
- **Contracts (`app/main.py` & `app/schemas/`)**: Authoritative Pydantic schemas registered via `flux.define_resource(...)` providing typed guarantees and schema export for frontend TypeScript generation.

```
       [ Client / Next.js Browser ]
                   │
                   │  HTTP (X-FluxFast: 1)
                   ▼
       ┌───────────────────────────────┐
       │     Routes (FluxRouter)       │
       │   app/routes/*_routes.py      │
       └───────┬───────────────┬───────┘
               │               │
      Page GET │               │ Mutation POST/PATCH
               ▼               ▼
       ┌──────────────┐ ┌──────────────┐
       │     Views    │ │ Controllers  │
       │  app/views/  │ │app/controllers│
       └───────┬──────┘ └──────┬───────┘
               │               │
               │ Fetch queries │ Transactions & Mutate
               └───────┬───────┘
                       ▼
       ┌───────────────────────────────┐
       │    Models (SQLAlchemy ORM)    │
       │         app/models/           │
       └───────────────┬───────────────┘
                       ▼
       ┌───────────────────────────────┐
       │       MySQL 8.4 Database      │
       │   (5 Relational Tables)       │
       └───────────────────────────────┘
```

---

## Relational Schema (5 MySQL Tables)

The project manages an e-commerce store with 5 relational MySQL tables:

1. **`categories`**: Product classifications (`id`, `slug`, `name`, `description`, `created_at`).
2. **`customers`**: Customer accounts (`id`, `email`, `name`, `tier`, `created_at`).
3. **`products`**: Inventory catalog with foreign key to categories (`id`, `category_id`, `sku`, `name`, `price`, `stock_quantity`, `is_active`, `created_at`).
4. **`orders`**: Customer purchases with foreign key to customers (`id`, `customer_id`, `order_number`, `status`, `total_amount`, `notes`, `created_at`, `updated_at`).
5. **`order_items`**: Order line items linking orders and products (`id`, `order_id`, `product_id`, `quantity`, `unit_price`, `subtotal`).

---

## Directory Structure

```
fluxfast-mvc-ecommerce/
├── app/
│   ├── __init__.py
│   ├── main.py                     # App factory, FluxFast init, resource contracts, router mounting
│   ├── core/
│   │   ├── config.py               # Pydantic BaseSettings (DATABASE_URL, DEBUG)
│   │   ├── database.py             # Async SQLAlchemy engine, session maker, get_db
│   │   └── seed.py                 # Initial data seeding
│   ├── models/                     # [M] SQLAlchemy ORM Models
│   │   ├── category.py
│   │   ├── customer.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── order_item.py
│   ├── views/                      # [V] FluxFast Page & Resource Builders
│   │   ├── dashboard_view.py
│   │   ├── product_view.py
│   │   └── order_view.py
│   ├── controllers/                # [C] Business Logic & Mutation Handlers
│   │   ├── dashboard_controller.py
│   │   ├── product_controller.py
│   │   └── order_controller.py
│   ├── routes/                     # FluxRouter HTTP and Protocol Endpoints
│   │   ├── dashboard_routes.py
│   │   ├── product_routes.py
│   │   └── order_routes.py
│   └── schemas/                    # Pydantic Schemas & DTOs
│       ├── category.py
│       ├── customer.py
│       ├── product.py
│       ├── order.py
│       └── dashboard.py
├── tests/
│   ├── conftest.py                 # Async test client & SQLite memory fixture
│   ├── test_pages.py               # FluxFast page contract & resource tests
│   ├── test_mutations.py           # Mutation patches & cache invalidation tests
│   └── test_mvc_structure.py       # Architectural boundary verification tests
├── docker-compose.yml              # Multi-container MySQL 8.4 + API setup
├── Dockerfile                      # Container build definition
├── init_db.sql                     # Raw MySQL DDL and seed dataset
├── pyproject.toml                  # Python package configuration
└── README.md
```

---

## Declaring and Using FluxFast in MVC

### 1. Declaring Typed Resource Contracts
In `app/main.py`, contracts are registered on the `FluxFast` instance:
```python
flux = FluxFast(app, debug=settings.DEBUG)

DASHBOARD_SUMMARY = flux.define_resource("dashboard-summary", DashboardSummary)
PRODUCT_CATALOG = flux.define_resource("product-catalog", list[ProductListItem])
CATEGORIES_LIST = flux.define_resource("categories-list", list[CategoryItem])
CUSTOMER_ORDERS = flux.define_resource("customer-orders", list[OrderSummary])
```

### 2. Building Views with Resources and Cache Scopes
In `app/views/order_view.py`, the view specifies component targets and user-isolated scopes:
```python
class OrderView:
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
```

### 3. Handling Mutations in Controllers
In `app/controllers/order_controller.py`, checkout deducts inventory transactionally and returns reactive patches and invalidations:
```python
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
```

### 4. Mounting Routes via FluxRouter
In `app/routes/product_routes.py`:
```python
router = FluxRouter(prefix="/products", tags=["products"])

@router.page("", name="products_catalog")
async def list_products(db: AsyncSession = Depends(get_db)) -> Page:
    return ProductView.render_catalog(db)

@router.mutation("", methods=["POST"], name="create_product")
async def create_product(payload: CreateProductInput, db: AsyncSession = Depends(get_db)) -> MutationResult:
    return await ProductController.create_product(db, payload)
```

---

## Getting Started

### 1. Local Development (Instant SQLite Zero-Config)
The application automatically defaults to SQLite if no `DATABASE_URL` is set:
```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` to view Swagger UI or send FluxFast protocol headers:
```bash
curl -H "X-FluxFast: 1" -H "X-FluxFast-Protocol: 1" http://localhost:8000/dashboard
```

### 2. Running with MySQL 8.4 via Docker Compose
To spin up MySQL and the application containers:
```bash
docker compose up --build
```
MySQL runs on port `33061` and automatically initializes `init_db.sql`. The API is accessible at `http://localhost:8000`.

### 3. Running Tests
Run the comprehensive test suite with `pytest`:
```bash
uv run pytest -v
```

### 4. Exporting Schema and Generating Frontend Types
```bash
# Export the offline schema manifest
uv run fluxfast schema app.main:app

# Generate frontend TypeScript contracts and validators
uv run fluxfast types app.main:app --frontend ../frontend
```
