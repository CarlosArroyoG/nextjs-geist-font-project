from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os
from routers import pos, lab_orders, inventory, users, reports, commissions, expenses
from error_handlers import register_error_handlers
from database import create_tables

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Optica POS Backend API",
    description="Backend services for Optical Store POS System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)

# Include all routers
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(pos.router, prefix="/api/pos", tags=["POS"])
app.include_router(lab_orders.router, prefix="/api/lab-orders", tags=["Lab Orders"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(commissions.router, prefix="/api/commissions", tags=["Commissions"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["Expenses"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.on_event("startup")
async def startup():
    # Create database tables
    create_tables()
    print("Starting up FastAPI backend...")

@app.on_event("shutdown")
async def shutdown():
    # Add cleanup tasks here
    print("Shutting down FastAPI backend...")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    )
