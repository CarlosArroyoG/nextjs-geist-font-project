from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from ..database import get_db
from ..models import Order, User
from datetime import datetime, timedelta
from .users import get_current_user

router = APIRouter()

# Commission rate (can be moved to environment variables or database settings)
COMMISSION_RATE = 0.05  # 5% commission

@router.get("/calculate")
async def calculate_commissions(
    start_date: str,
    end_date: str,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate commissions for a specific period and optionally for a specific user
    """
    if not current_user.is_admin:
        # Non-admin users can only view their own commissions
        user_id = current_user.id

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    # Base query for completed orders in the date range
    query = db.query(
        User.id,
        User.username,
        User.full_name,
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total_amount).label('total_sales')
    ).join(
        Order
    ).filter(
        and_(
            Order.created_at >= start,
            Order.created_at < end,
            Order.status == 'completed'
        )
    )

    if user_id:
        query = query.filter(User.id == user_id)

    results = query.group_by(
        User.id,
        User.username,
        User.full_name
    ).all()

    commission_data = []
    for row in results:
        total_sales = float(row.total_sales or 0)
        commission_amount = total_sales * COMMISSION_RATE
        commission_data.append({
            "user_id": row.id,
            "username": row.username,
            "full_name": row.full_name,
            "total_orders": row.total_orders,
            "total_sales": total_sales,
            "commission_rate": COMMISSION_RATE,
            "commission_amount": commission_amount
        })

    return {
        "start_date": start_date,
        "end_date": end_date,
        "commission_rate": COMMISSION_RATE,
        "commissions": commission_data
    }

@router.get("/summary")
async def get_commission_summary(
    period: str = "month",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get commission summary for different periods (week, month, year)
    """
    now = datetime.utcnow()
    
    if period == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid period. Use week, month, or year"
        )

    # For non-admin users, only show their own commission
    query = db.query(
        User.id,
        User.username,
        User.full_name,
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total_amount).label('total_sales')
    ).join(
        Order
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= now,
            Order.status == 'completed'
        )
    )

    if not current_user.is_admin:
        query = query.filter(User.id == current_user.id)

    results = query.group_by(
        User.id,
        User.username,
        User.full_name
    ).all()

    commission_data = []
    total_commission = 0
    for row in results:
        total_sales = float(row.total_sales or 0)
        commission_amount = total_sales * COMMISSION_RATE
        total_commission += commission_amount
        commission_data.append({
            "user_id": row.id,
            "username": row.username,
            "full_name": row.full_name,
            "total_orders": row.total_orders,
            "total_sales": total_sales,
            "commission_amount": commission_amount
        })

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "commission_rate": COMMISSION_RATE,
        "total_commission": total_commission,
        "commissions": commission_data
    }

@router.get("/top-performers")
async def get_top_performers(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get top performing users based on sales and commissions
    Admin only endpoint
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this information"
        )

    query = db.query(
        User.id,
        User.username,
        User.full_name,
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total_amount).label('total_sales')
    ).join(
        Order
    ).filter(
        Order.status == 'completed'
    )

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(
                and_(
                    Order.created_at >= start,
                    Order.created_at < end
                )
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

    results = query.group_by(
        User.id,
        User.username,
        User.full_name
    ).order_by(
        func.sum(Order.total_amount).desc()
    ).limit(limit).all()

    performers_data = []
    for row in results:
        total_sales = float(row.total_sales or 0)
        commission_amount = total_sales * COMMISSION_RATE
        performers_data.append({
            "user_id": row.id,
            "username": row.username,
            "full_name": row.full_name,
            "total_orders": row.total_orders,
            "total_sales": total_sales,
            "commission_amount": commission_amount
        })

    return {
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "commission_rate": COMMISSION_RATE,
        "top_performers": performers_data
    }
