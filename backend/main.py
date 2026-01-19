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


@asynccontextmanager
async def lifespan(app: FastAPI):

    retries = 10
    while retries:
        try:
            # ONLY create tables (no data insertion)
            database_model.Base.metadata.create_all(bind=engine)
            print("Database ready")
            break
        except OperationalError:
            retries -= 1
            print("Waiting for DB...")
            time.sleep(2)

    if retries == 0:
        raise RuntimeError("Database not reachable")

    yield


# -------------------------
# App
# -------------------------
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return db_product


@app.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    db_product = db.query(database_model.Product).filter(database_model.Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}
