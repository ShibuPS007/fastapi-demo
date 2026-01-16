import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from database import SessionLocal, engine
import database_model
from models import Product


# -------------------------
# Seed data
# -------------------------
PRODUCTS = [
    Product(id=1, name="Phone", description="A smartphone", price=699.99, quantity=50),
    Product(id=2, name="Laptop", description="A powerful laptop", price=999.99, quantity=30),
    Product(id=6, name="Pen", description="A blue ink pen", price=1.99, quantity=100),
    Product(id=7, name="Table", description="A wooden table", price=199.99, quantity=20),
]


# -------------------------
# DB init (NEVER auto-run)
# -------------------------
def init_db():
    db = SessionLocal()
    try:
        count = db.query(database_model.Product).count()
        if count == 0:
            for product in PRODUCTS:
                db.add(database_model.Product(**product.model_dump()))
            db.commit()
    finally:
        db.close()


# -------------------------
# Lifespan (startup/shutdown)
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):

    # ⛔ Skip DB during pytest
    if os.getenv("TESTING") != "true":
        retries = 10
        while retries:
            try:
                database_model.Base.metadata.create_all(bind=engine)
                init_db()
                print("✅ Database initialized")
                break
            except OperationalError:
                retries -= 1
                print("⏳ Waiting for DB...")
                time.sleep(2)

        if retries == 0:
            raise RuntimeError("❌ Database not reachable")

    yield
    # optional shutdown cleanup


# -------------------------
# App
# -------------------------
app = FastAPI(lifespan=lifespan)

origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Dependencies
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Routes
# -------------------------
@app.get("/")
def greet():
    return "Welcome to Telusko Trac"


@app.get("/products")
def get_all_products(db: Session = Depends(get_db)):
    return db.query(database_model.Product).all()


@app.get("/products/{id}")
def get_product_by_id(id: int, db: Session = Depends(get_db)):
    product = db.query(database_model.Product).filter(database_model.Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products")
def add_product(product: Product, db: Session = Depends(get_db)):
    db_product = database_model.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.put("/products/{id}")
def update_product(id: int, product: Product, db: Session = Depends(get_db)):
    db_product = db.query(database_model.Product).filter(database_model.Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_product.name = product.name
    db_product.description = product.description
    db_product.price = product.price
    db_product.quantity = product.quantity

    db.commit()
    db.refresh(db_product)
    return {"message": "Product updated successfully", "product": db_product}


@app.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    db_product = db.query(database_model.Product).filter(database_model.Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}
