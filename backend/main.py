from fastapi import Depends,FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Product
from database import SessionLocal,engine
import database_model
from sqlalchemy.orm import Session
import os


app=FastAPI()
origins = os.getenv("CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database_model.Base.metadata.create_all(bind=engine)
@app.get("/")
def greet():
    return "Welcome to telusko Trac"


Products= [
    Product(id=1, name="Phone", description="A smartphone", price=699.99, quantity=50),
    Product(id=2, name="Laptop", description="A powerful laptop", price=999.99, quantity=30),
    Product(id=6, name="Pen", description="A blue ink pen", price=1.99, quantity=100),
    Product(id=7, name="Table", description="A wooden table", price=199.99, quantity=20),
]


def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    db= SessionLocal()

    count=db.query(database_model.Product).count()

    if count==0:
        for product in Products:
            db.add(database_model.Product(**product.model_dump()))

    db.commit()
init_db()



@app.get("/products")
def get_all_products(db:Session=Depends(get_db)):
    # db=SessionLocal()
    # db.query()
    db_products=db.query(database_model.Product).all()
    return db_products

@app.get("/products/{id}")
def get_product_by_id(id:int,db:Session=Depends(get_db)):
    db_product=db.query(database_model.Product).filter(database_model.Product.id==id).first()
    if db_product:
         return db_product
    return "product not found"


@app.post("/products")
def add_product(product:Product,db:Session=Depends(get_db)):
    db.add(database_model.Product(**product.model_dump()))
    db.commit()
    return product 

@app.put("/products/{id}")
def update_product(id:int,product:Product,db:Session=Depends(get_db)):
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


@app.delete("/products")
def delete_product(id:int,db:Session=Depends(get_db)):
    db_product = db.query(database_model.Product).filter(database_model.Product.id ==id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}