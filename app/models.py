from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    password = Column(String)  # hashed password
    role = Column(String)  # Admin/Buyer/Seller
    products = relationship('Product', back_populates='seller')
    orders = relationship('Order', back_populates='buyer')

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    date_created = Column(DateTime, default=datetime.utcnow)
    available_qty = Column(Integer)
    seller_id = Column(Integer, ForeignKey('users.id'))
    seller = relationship('User', back_populates='products')

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey('users.id'))
    date_ordered = Column(DateTime, default=datetime.utcnow)
    items = Column(String)  # JSON or structured representation of items
    order_total = Column(Float)
    status = Column(String)  # Active, Shipped, Completed, Canceled
    buyer = relationship('User', back_populates='orders')

class Cart(Base):
    __tablename__ = 'cart'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    qty = Column(Integer)
