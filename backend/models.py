from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID, uuid4

# Association table for order items
order_items = Table(
    'order_items',
    Base.metadata,
    Column('order_id', Integer, ForeignKey('orders.id')),
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('quantity', Integer),
    Column('price_at_time', Float)
)

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    price = Column(Float)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    status = Column(String)  # pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    products = relationship("Product", secondary=order_items)
    prescription = relationship("Prescription", back_populates="order", uselist=False)

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    
    # Right Eye
    right_eye_sphere = Column(String)
    right_eye_cylinder = Column(String)
    right_eye_axis = Column(String)
    right_eye_add = Column(String)
    
    # Left Eye
    left_eye_sphere = Column(String)
    left_eye_cylinder = Column(String)
    left_eye_axis = Column(String)
    left_eye_add = Column(String)
    
    # Additional Details
    material = Column(String)
    treatment = Column(String)
    requires_add = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order = relationship("Order", back_populates="prescription")

class LabOrder(Base):
    __tablename__ = "lab_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    status = Column(String)  # pending, in-progress, completed, cancelled
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    prescription = relationship("Prescription")

# Pydantic Models for API
class UserBase(BaseModel):
    email: str
    username: str
    full_name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PrescriptionBase(BaseModel):
    right_eye_sphere: str
    right_eye_cylinder: str
    right_eye_axis: str
    right_eye_add: Optional[str]
    left_eye_sphere: str
    left_eye_cylinder: str
    left_eye_axis: str
    left_eye_add: Optional[str]
    material: str
    treatment: str
    requires_add: bool = False
    notes: Optional[str]

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionResponse(PrescriptionBase):
    id: int
    order_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemBase]
    prescription: Optional[PrescriptionCreate]

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    prescription: Optional[PrescriptionResponse]

    class Config:
        orm_mode = True

class LabOrderBase(BaseModel):
    prescription_id: int
    status: str
    notes: Optional[str]

class LabOrderCreate(LabOrderBase):
    pass

class LabOrderResponse(LabOrderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
