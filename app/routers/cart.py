from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..models import Cart, Product, User
from ..schemas import CartItem, CartOut
from ..database import get_db
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ..config import SECRET_KEY, ALGORITHM

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

@router.post("/", response_model=CartOut)
def add_to_cart(
    cart_item: CartItem, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == cart_item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.available_qty < cart_item.qty:
        raise HTTPException(status_code=400, detail="Insufficient product quantity")

    # Check if the item is already in the cart
    cart_entry = db.query(Cart).filter(Cart.user_id == current_user.id, Cart.product_id == cart_item.product_id).first()
    if cart_entry:
        # Update quantity if the item exists in the cart
        cart_entry.qty += cart_item.qty
    else:
        # Add new item to the cart
        new_cart_item = Cart(user_id=current_user.id, product_id=cart_item.product_id, qty=cart_item.qty)
        db.add(new_cart_item)

    db.commit()
    return {"user_id": current_user.id, "product_id": cart_item.product_id, "qty": cart_item.qty}

@router.get("/", response_model=List[CartOut])
def view_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    return cart_items

@router.delete("/{product_id}")
def remove_from_cart(
    product_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    cart_entry = db.query(Cart).filter(Cart.user_id == current_user.id, Cart.product_id == product_id).first()
    if not cart_entry:
        raise HTTPException(status_code=404, detail="Product not found in the cart")
    
    db.delete(cart_entry)
    db.commit()
    return {"detail": "Product removed from cart"}

@router.put("/{product_id}", response_model=CartOut)
def update_cart(
    product_id: int, 
    qty: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    cart_entry = db.query(Cart).filter(Cart.user_id == current_user.id, Cart.product_id == product_id).first()
    if not cart_entry:
        raise HTTPException(status_code=404, detail="Product not found in the cart")
    
    if qty <= 0:
        db.delete(cart_entry)
        db.commit()
        return {"detail": "Product removed from cart due to zero quantity"}

    cart_entry.qty = qty
    db.commit()
    db.refresh(cart_entry)
    return cart_entry
