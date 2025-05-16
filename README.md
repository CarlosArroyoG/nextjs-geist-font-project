# Optica POS Backend API

FastAPI backend for the Optical Store POS System. This API provides endpoints for managing products, orders, prescriptions, lab orders, inventory, users, reports, commissions, and expenses.

## Features

- 🛍️ **POS System**: Manage products and orders
- 👁️ **Lab Orders**: Handle prescriptions and lab work orders
- 📦 **Inventory Management**: Track product stock and movements
- 👥 **User Management**: Authentication and authorization
- 📊 **Reports**: Generate sales and inventory reports
- 💰 **Commissions**: Calculate and track sales commissions
- 💵 **Expenses**: Manage business expenses

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory:
```env
DATABASE_URL=sqlite:///./optica.db  # For SQLite
# DATABASE_URL=postgresql://user:password@localhost/dbname  # For PostgreSQL
SECRET_KEY=your-secret-key-here
```

4. Run the application:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

### Users
- POST `/api/users/token` - Login and get access token
- POST `/api/users/register` - Register new user
- GET `/api/users/me` - Get current user info
- PUT `/api/users/me` - Update current user

### POS
- GET `/api/pos/products` - List products
- POST `/api/pos/orders` - Create new order
- GET `/api/pos/orders` - List orders
- GET `/api/pos/orders/{order_id}` - Get order details

### Lab Orders
- GET `/api/lab-orders` - List lab orders
- POST `/api/lab-orders` - Create new lab order
- GET `/api/lab-orders/{lab_order_id}` - Get lab order details
- PUT `/api/lab-orders/{lab_order_id}/status` - Update lab order status

### Inventory
- GET `/api/inventory` - List inventory
- POST `/api/inventory` - Add new product
- PUT `/api/inventory/{product_id}` - Update product
- PATCH `/api/inventory/{product_id}/stock` - Update stock
- GET `/api/inventory/stats` - Get inventory statistics

### Reports
- GET `/api/reports/sales/daily` - Daily sales report
- GET `/api/reports/sales/monthly` - Monthly sales report
- GET `/api/reports/inventory/movement` - Inventory movement report
- GET `/api/reports/sales/summary` - Sales summary

### Commissions
- GET `/api/commissions/calculate` - Calculate commissions
- GET `/api/commissions/summary` - Commission summary
- GET `/api/commissions/top-performers` - Top performing users

### Expenses
- POST `/api/expenses` - Add new expense
- GET `/api/expenses` - List expenses
- GET `/api/expenses/summary` - Expense summary
- GET `/api/expenses/categories` - List expense categories

## Authentication

Most endpoints require authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <your-access-token>
```

## Development

### Project Structure
```
backend/
├── routers/
│   ├── pos.py
│   ├── lab_orders.py
│   ├── inventory.py
│   ├── users.py
│   ├── reports.py
│   ├── commissions.py
│   └── expenses.py
├── models.py
├── database.py
├── main.py
├── error_handlers.py
└── requirements.txt
```

### Adding New Features

1. Create new models in `models.py`
2. Create new router in `routers/`
3. Include router in `main.py`
4. Update documentation

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Server Error

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
