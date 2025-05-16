from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import (
    LabOrder, Prescription, 
    LabOrderCreate, LabOrderResponse,
    PrescriptionCreate, PrescriptionResponse
)
from datetime import datetime

router = APIRouter()

# Lab Orders endpoints
@router.get("/", response_model=List[LabOrderResponse])
async def get_lab_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Get list of lab orders with optional status filter and pagination
    """
    query = db.query(LabOrder)
    
    if status:
        valid_statuses = ["pending", "in-progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        query = query.filter(LabOrder.status == status)
    
    lab_orders = query.offset(skip).limit(limit).all()
    return lab_orders

@router.post("/", response_model=LabOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_order(
    lab_order: LabOrderCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new lab order
    """
    # Verify prescription exists
    prescription = db.query(Prescription).filter(
        Prescription.id == lab_order.prescription_id
    ).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )

    # Create lab order
    db_lab_order = LabOrder(**lab_order.dict())
    db.add(db_lab_order)
    
    try:
        db.commit()
        db.refresh(db_lab_order)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return db_lab_order

@router.get("/{lab_order_id}", response_model=LabOrderResponse)
async def get_lab_order(lab_order_id: int, db: Session = Depends(get_db)):
    """
    Get a specific lab order by ID
    """
    lab_order = db.query(LabOrder).filter(LabOrder.id == lab_order_id).first()
    if not lab_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab order not found"
        )
    return lab_order

@router.put("/{lab_order_id}/status")
async def update_lab_order_status(
    lab_order_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update lab order status
    """
    valid_statuses = ["pending", "in-progress", "completed", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    lab_order = db.query(LabOrder).filter(LabOrder.id == lab_order_id).first()
    if not lab_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab order not found"
        )

    lab_order.status = status
    lab_order.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(lab_order)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {"message": "Lab order status updated successfully"}

@router.put("/{lab_order_id}/notes")
async def update_lab_order_notes(
    lab_order_id: int,
    notes: str,
    db: Session = Depends(get_db)
):
    """
    Update lab order notes
    """
    lab_order = db.query(LabOrder).filter(LabOrder.id == lab_order_id).first()
    if not lab_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab order not found"
        )

    lab_order.notes = notes
    lab_order.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(lab_order)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {"message": "Lab order notes updated successfully"}

# Prescription endpoints
@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription(prescription_id: int, db: Session = Depends(get_db)):
    """
    Get a specific prescription by ID
    """
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id
    ).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )
    return prescription

@router.put("/prescriptions/{prescription_id}")
async def update_prescription(
    prescription_id: int,
    prescription_update: PrescriptionCreate,
    db: Session = Depends(get_db)
):
    """
    Update prescription details
    """
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id
    ).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )

    # Update prescription fields
    for field, value in prescription_update.dict().items():
        setattr(prescription, field, value)
    
    prescription.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(prescription)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {"message": "Prescription updated successfully"}
