from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Product, ProductCreate, ProductResponse
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
async def get_inventory(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    min_stock: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get inventory list with optional filters and pagination
    """
    query = db.query(Product)
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    if min_stock is not None:
        query = query.filter(Product.stock <= min_stock)
    
    products = query.order_by(Product.stock.asc()).offset(skip).limit(limit).all()
    return products

@router.get("/low-stock", response_model=List[ProductResponse])
async def get_low_stock_products(
    threshold: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get products with stock below specified threshold
    """
    products = db.query(Product).filter(Product.stock <= threshold).all()
    return products

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def add_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new product to inventory
    """
    # Check if product with same name exists
    existing_product = db.query(Product).filter(Product.name == product.name).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this name already exists"
        )

    db_product = Product(**product.dict())
    db.add(db_product)
    
    try:
        db.commit()
        db.refresh(db_product)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return db_product

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Update product details
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Check if name is being changed and if new name already exists
    if product_update.name != db_product.name:
        existing_product = db.query(Product).filter(Product.name == product_update.name).first()
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this name already exists"
            )

    # Update product fields
    for field, value in product_update.dict().items():
        setattr(db_product, field, value)
    
    db_product.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_product)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return db_product

@router.patch("/{product_id}/stock")
async def update_stock(
    product_id: int,
    quantity: int,
    operation: str,
    db: Session = Depends(get_db)
):
    """
    Update product stock (increase/decrease)
    """
    valid_operations = ["increase", "decrease"]
    if operation not in valid_operations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation. Must be one of: {', '.join(valid_operations)}"
        )

    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if operation == "decrease" and db_product.stock < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock"
        )

    if operation == "increase":
        db_product.stock += quantity
    else:  # decrease
        db_product.stock -= quantity

    db_product.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_product)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {
        "message": "Stock updated successfully",
        "new_stock": db_product.stock
    }

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a product from inventory
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    try:
        db.delete(db_product)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {"message": "Product deleted successfully"}

@router.get("/stats")
async def get_inventory_stats(db: Session = Depends(get_db)):
    """
    Get inventory statistics
    """
    total_products = db.query(Product).count()
    total_stock = db.query(Product).with_entities(
        db.func.sum(Product.stock)
    ).scalar() or 0
    low_stock_count = db.query(Product).filter(Product.stock <= 10).count()
    out_of_stock = db.query(Product).filter(Product.stock == 0).count()

    return {
        "total_products": total_products,
        "total_stock": total_stock,
        "low_stock_count": low_stock_count,
        "out_of_stock": out_of_stock
    }
