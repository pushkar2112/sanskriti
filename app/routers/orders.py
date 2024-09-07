from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..models import Order, Cart, Product, User
from ..schemas import OrderCreate, OrderOut
from ..database import get_db
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ..config import SECRET_KEY, ALGORITHM
from datetime import datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/", response_model=OrderOut)
def place_order(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Fetch cart items for the current user
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order_total = 0
    order_items = []

    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product or product.available_qty < item.qty:
            raise HTTPException(
                status_code=400,
                detail=f"Product {product.name} has insufficient stock"
            )
        # Update product quantity
        product.available_qty -= item.qty
        order_total += product.price * item.qty
        order_items.append({"product_id": product.id, "qty": item.qty})

    # Create the order
    new_order = Order(
        buyer_id=current_user.id,
        items=order_items,
        order_total=order_total
    )
    db.add(new_order)
    # Clear the cart after order is placed
    db.query(Cart).filter(Cart.user_id == current_user.id).delete()
    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/active", response_model=List[OrderOut])
def get_active_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    active_orders = db.query(Order).filter(Order.buyer_id == current_user.id, Order.status == "active").all()
    return active_orders

@router.get("/past", response_model=List[OrderOut])
def get_past_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    past_orders = db.query(Order).filter(Order.buyer_id == current_user.id, Order.status == "completed").all()
    return past_orders

@router.get("/{order_id}", response_model=OrderOut)
def get_order_details(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.delete("/{order_id}")
def cancel_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id, Order.status == "active").first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or already completed")

    # Revert stock for canceled order items
    for item in order.items:
        product = db.query(Product).filter(Product.id == item["product_id"]).first()
        product.available_qty += item["qty"]

    order.status = "canceled"
    db.commit()
    return {"detail": "Order canceled successfully"}
