from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: Optional[str] = 'Buyer'

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    role: str

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    available_qty: int

class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int
    date_created: datetime
    seller_id: int

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    items: List[dict]  # Adjust type as per your design
    order_total: float
    status: Optional[str] = 'Active'

class OrderCreate(OrderBase):
    pass

class OrderOut(OrderBase):
    id: int
    buyer_id: int
    date_ordered: datetime

    class Config:
        orm_mode = True

class CartItem(BaseModel):
    product_id: int
    qty: int

class CartOut(CartItem):
    user_id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
