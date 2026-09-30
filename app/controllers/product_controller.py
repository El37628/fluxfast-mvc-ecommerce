from fastapi import HTTPException
from fluxfast import (
    MutationResult,
    append_item,
    invalidate_resource,
    mutation,
    replace_item,
    scope,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, Product
from app.schemas import (
    CategoryItem,
    CreateProductInput,
    ProductDetail,
    ProductListItem,
    UpdateStockInput,
)


class ProductController:
    """Controller handling catalog queries and product mutations."""

    @staticmethod
    async def get_categories(db: AsyncSession) -> list[CategoryItem]:
        # Count products per category
        stmt = (
            select(
                Category.id,
                Category.slug,
                Category.name,
                Category.description,
                func.count(Product.id).label("prod_cnt"),
            )
            .outerjoin(Product, Product.category_id == Category.id)
            .group_by(Category.id)
            .order_by(Category.name.asc())
        )
        res = await db.execute(stmt)
        return [
            CategoryItem(
                id=row[0],
                slug=row[1],
                name=row[2],
                description=row[3],
                product_count=row[4],
            )
            for row in res.all()
        ]

    @staticmethod
    async def get_catalog(
        db: AsyncSession,
        category_id: int | None = None,
        search: str | None = None,
    ) -> list[ProductListItem]:
        stmt = select(Product).options(selectinload(Product.category))
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if search:
            stmt = stmt.where(
                Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%")
            )
        stmt = stmt.order_by(Product.name.asc())
        res = await db.execute(stmt)
        return [
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
            for p in res.scalars().all()
        ]

    @staticmethod
    async def get_product(db: AsyncSession, product_id: int) -> ProductDetail:
        stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        res = await db.execute(stmt)
        product = res.scalars().first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return ProductDetail(
            id=product.id,
            sku=product.sku,
            name=product.name,
            category_id=product.category_id,
            category_name=product.category.name if product.category else "Unassigned",
            price=product.price,
            stock_quantity=product.stock_quantity,
            is_active=product.is_active,
            created_at=product.created_at.isoformat(),
        )

    @staticmethod
    async def create_product(
        db: AsyncSession,
        payload: CreateProductInput,
    ) -> MutationResult:
        # Check category existence
        cat_res = await db.execute(select(Category).where(Category.id == payload.category_id))
        category = cat_res.scalars().first()
        if not category:
            raise HTTPException(status_code=400, detail="Category does not exist")

        # Check sku unique
        sku_res = await db.execute(select(Product).where(Product.sku == payload.sku))
        if sku_res.scalars().first():
            raise HTTPException(status_code=400, detail="Product SKU already exists")

        new_product = Product(
            sku=payload.sku,
            name=payload.name,
            category_id=payload.category_id,
            price=payload.price,
            stock_quantity=payload.stock_quantity,
            is_active=True,
        )
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)

        item = ProductListItem(
            id=new_product.id,
            sku=new_product.sku,
            name=new_product.name,
            category_id=new_product.category_id,
            category_name=category.name,
            price=new_product.price,
            stock_quantity=new_product.stock_quantity,
            is_active=new_product.is_active,
        )

        return mutation(
            patches={
                "product-catalog": [append_item(item.model_dump(mode="json"))]
            },
            invalidates=[
                invalidate_resource("dashboard-summary", scope=scope.public()),
                invalidate_resource("categories-list", scope=scope.public()),
            ],
        )

    @staticmethod
    async def update_stock(
        db: AsyncSession,
        product_id: int,
        payload: UpdateStockInput,
    ) -> MutationResult:
        stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        res = await db.execute(stmt)
        product = res.scalars().first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        product.stock_quantity = payload.stock_quantity
        await db.commit()
        await db.refresh(product)

        updated_item = ProductListItem(
            id=product.id,
            sku=product.sku,
            name=product.name,
            category_id=product.category_id,
            category_name=product.category.name if product.category else "Unassigned",
            price=product.price,
            stock_quantity=product.stock_quantity,
            is_active=product.is_active,
        )

        return mutation(
            patches={
                "product-catalog": [replace_item(product.id, updated_item.model_dump(mode="json"))]
            },
            invalidates=[
                invalidate_resource("dashboard-summary", scope=scope.public()),
                invalidate_resource(f"product-detail-{product.id}", scope=scope.public()),
            ],
        )
