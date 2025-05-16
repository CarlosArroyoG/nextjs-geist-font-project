from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from ..database import get_db
from ..models import Order, Product, User
from datetime import datetime, timedelta
from .users import get_current_user

router = APIRouter()

@router.get("/sales/daily")
async def get_daily_sales(
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get daily sales report
    """
    try:
        if date:
            report_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            report_date = datetime.utcnow()

        start_date = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        # Get total sales and order count
        sales_data = db.query(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total_amount).label('total_sales')
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status == 'completed'
            )
        ).first()

        # Get hourly breakdown
        hourly_sales = db.query(
            func.date_part('hour', Order.created_at).label('hour'),
            func.count(Order.id).label('orders'),
            func.sum(Order.total_amount).label('sales')
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status == 'completed'
            )
        ).group_by(
            func.date_part('hour', Order.created_at)
        ).all()

        return {
            "date": start_date.date().isoformat(),
            "total_orders": sales_data[0] or 0,
            "total_sales": float(sales_data[1] or 0),
            "hourly_breakdown": [
                {
                    "hour": int(row[0]),
                    "orders": row[1],
                    "sales": float(row[2] or 0)
                }
                for row in hourly_sales
            ]
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

@router.get("/sales/monthly")
async def get_monthly_sales(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get monthly sales report
    """
    try:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # Get total sales and order count
        sales_data = db.query(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total_amount).label('total_sales')
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status == 'completed'
            )
        ).first()

        # Get daily breakdown
        daily_sales = db.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('orders'),
            func.sum(Order.total_amount).label('sales')
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status == 'completed'
            )
        ).group_by(
            func.date(Order.created_at)
        ).all()

        return {
            "year": year,
            "month": month,
            "total_orders": sales_data[0] or 0,
            "total_sales": float(sales_data[1] or 0),
            "daily_breakdown": [
                {
                    "date": row[0].isoformat(),
                    "orders": row[1],
                    "sales": float(row[2] or 0)
                }
                for row in daily_sales
            ]
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid year or month"
        )

@router.get("/inventory/movement")
async def get_inventory_movement(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get inventory movement report
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        # Get products sold in the period
        products_movement = db.query(
            Product.id,
            Product.name,
            func.count(Order.id).label('times_sold'),
            func.sum(Order.total_amount).label('total_revenue')
        ).join(
            Order, Product.orders
        ).filter(
            and_(
                Order.created_at >= start,
                Order.created_at < end,
                Order.status == 'completed'
            )
        ).group_by(
            Product.id
        ).all()

        return {
            "start_date": start_date,
            "end_date": end_date,
            "products": [
                {
                    "id": row[0],
                    "name": row[1],
                    "times_sold": row[2],
                    "total_revenue": float(row[3] or 0)
                }
                for row in products_movement
            ]
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

@router.get("/inventory/low-stock")
async def get_low_stock_report(
    threshold: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get low stock inventory report
    """
    low_stock_products = db.query(
        Product
    ).filter(
        Product.stock <= threshold
    ).order_by(
        Product.stock.asc()
    ).all()

    return {
        "threshold": threshold,
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "current_stock": product.stock,
                "last_updated": product.updated_at.isoformat()
            }
            for product in low_stock_products
        ]
    }

@router.get("/sales/top-products")
async def get_top_products(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get top selling products report
    """
    query = db.query(
        Product.id,
        Product.name,
        func.count(Order.id).label('times_sold'),
        func.sum(Order.total_amount).label('total_revenue')
    ).join(
        Order, Product.orders
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

    top_products = query.group_by(
        Product.id
    ).order_by(
        func.count(Order.id).desc()
    ).limit(limit).all()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "products": [
            {
                "id": row[0],
                "name": row[1],
                "times_sold": row[2],
                "total_revenue": float(row[3] or 0)
            }
            for row in top_products
        ]
    }

@router.get("/sales/summary")
async def get_sales_summary(
    period: str = "week",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get sales summary for different periods (day, week, month, year)
    """
    now = datetime.utcnow()
    
    if period == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid period. Use day, week, month, or year"
        )

    sales_data = db.query(
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total_amount).label('total_sales'),
        func.avg(Order.total_amount).label('average_order_value')
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= now,
            Order.status == 'completed'
        )
    ).first()

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "total_orders": sales_data[0] or 0,
        "total_sales": float(sales_data[1] or 0),
        "average_order_value": float(sales_data[2] or 0)
    }
