from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

import models
from database import engine, get_db
from schemas import ProductCreate, ProductOut, ProductQuantityUpdate, StockUpdate

app = FastAPI()


@app.get("/")
def index() -> dict:
    return {
        "message": "Welcome to Inventory Management System",
        "detail": "For detailed information on available APIs, access /docs.",
    }


def print_greeting() -> None:
    print("inventory-management-system")


def db_is_up() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def ensure_tables() -> None:
    # Importing models registers SQLAlchemy models on models.Base
    models.Base.metadata.create_all(bind=engine)


def get_db_with_checks(db: Session = Depends(get_db)) -> Session:
    """Dependency that checks DB connection and ensures tables exist."""
    if not db_is_up():
        raise HTTPException(status_code=500, detail="Database connection failed")
    ensure_tables()
    return db


def get_product_or_404(product_id: int, db: Session) -> models.Product:
    """Get product by ID or raise 404 if not found."""
    product = db.get(models.Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def update_and_return_product(product: models.Product, db: Session) -> ProductOut:
    """Commit changes and return product as ProductOut."""
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductOut(id=product.id, name=product.name, quantity=product.quantity)


@app.post("/products", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db_with_checks)):
    product = models.Product(name=payload.name, quantity=payload.quantity)
    return update_and_return_product(product, db)


@app.get("/products", response_model=List[ProductOut])
def get_products(db: Session = Depends(get_db_with_checks)):
    stmt = select(models.Product).order_by(models.Product.id)
    rows = db.execute(stmt).scalars().all()
    return [ProductOut(id=p.id, name=p.name, quantity=p.quantity) for p in rows]


@app.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductQuantityUpdate,
    db: Session = Depends(get_db_with_checks),
):
    product = get_product_or_404(product_id, db)
    product.quantity = payload.quantity
    return update_and_return_product(product, db)


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db_with_checks)):
    product = get_product_or_404(product_id, db)
    db.delete(product)
    db.commit()
    return None


@app.post("/inventory/add", response_model=ProductOut)
def receive_stock(payload: StockUpdate, db: Session = Depends(get_db_with_checks)):
    product = get_product_or_404(payload.productId, db)
    product.quantity += payload.quantity
    return update_and_return_product(product, db)


@app.post("/inventory/remove", response_model=ProductOut)
def sell_stock(payload: StockUpdate, db: Session = Depends(get_db_with_checks)):
    product = get_product_or_404(payload.productId, db)
    if product.quantity < payload.quantity:
        raise HTTPException(status_code=400, detail="insufficient stock")
    product.quantity -= payload.quantity
    return update_and_return_product(product, db)


def main() -> None:
    print_greeting()

    if not db_is_up():
        print("DB connection failed (create the DB / fix credentials).")
        return

    ensure_tables()
    print("DB tables ensured.")


if __name__ == "__main__":
    main()
