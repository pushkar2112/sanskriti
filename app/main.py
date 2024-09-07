from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, products, cart, orders

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Including Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(cart.router, prefix="/cart", tags=["Cart"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])

# Health Check
@app.get("/")
def read_root():
    return {"message": "E-commerce API is running"}
