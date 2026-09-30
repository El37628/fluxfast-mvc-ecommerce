from pydantic import BaseModel


class CategoryItem(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None = None
    product_count: int = 0
