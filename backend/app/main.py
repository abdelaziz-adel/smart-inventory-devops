from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from io import StringIO
import csv
from pydantic import BaseModel, Field, ConfigDict
from prometheus_client import Counter, CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select
from sqlalchemy.orm import Mapped, Session, mapped_column
from .database import Base, engine, get_db

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(default=0)
    min_stock: Mapped[int] = mapped_column(default=5)
    price: Mapped[float] = mapped_column(default=0)

class ProductInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)
    min_stock: int = Field(ge=0)
    price: float = Field(ge=0)

class ProductOutput(ProductInput):
    id: int
    model_config = ConfigDict(from_attributes=True)

operations = Counter("inventory_operations_total", "Inventory create/update/delete requests", ["operation"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Inventory API", lifespan=lifespan)
Db = Annotated[Session, Depends(get_db)]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/products", response_model=list[ProductOutput])
def list_products(db: Db):
    return db.scalars(select(Product).order_by(Product.id)).all()

@app.get("/products/low-stock", response_model=list[ProductOutput])
def low_stock(db: Db):
    return db.scalars(select(Product).where(Product.quantity <= Product.min_stock).order_by(Product.id)).all()

@app.post("/products", response_model=ProductOutput, status_code=201)
def create_product(item: ProductInput, db: Db):
    product = Product(**item.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    operations.labels(operation="create").inc()
    return product

@app.put("/products/{product_id}", response_model=ProductOutput)
def update_product(product_id: int, item: ProductInput, db: Db):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    for field, value in item.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    operations.labels(operation="update").inc()
    return product

@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Db):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    db.delete(product)
    db.commit()
    operations.labels(operation="delete").inc()

@app.get("/reports/summary")
def report_summary(db: Db):
    products = db.scalars(select(Product)).all()
    return {
        "total_products": len(products),
        "low_stock_products": sum(p.quantity <= p.min_stock for p in products),
        "total_units": sum(p.quantity for p in products),
        "total_inventory_value": round(sum(p.quantity * p.price for p in products), 2),
    }

@app.get("/reports/inventory.csv")
def inventory_csv(db: Db):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "quantity", "min_stock", "price", "low_stock"])
    for p in db.scalars(select(Product).order_by(Product.id)).all():
        writer.writerow([p.id, p.name, p.quantity, p.min_stock, p.price, p.quantity <= p.min_stock])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=inventory-report.csv"})
