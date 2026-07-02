from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    quantity: int


class ProductOut(BaseModel):
    id: int
    name: str
    quantity: int


class ProductQuantityUpdate(BaseModel):
    quantity: int


class StockUpdate(BaseModel):
    productId: int
    quantity: int