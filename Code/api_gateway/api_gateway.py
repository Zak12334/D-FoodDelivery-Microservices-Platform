import os
import grpc
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Create FastAPI app
app = FastAPI(title="Food Delivery API Gateway")

# Service addresses 
ORDER_SERVICE_ADDRESS = os.getenv("ORDER_SERVICE_ADDRESS", "order-service:50051")
PAYMENT_SERVICE_ADDRESS = os.getenv("PAYMENT_SERVICE_ADDRESS", "payment-service:50052")

# model for API requests/responses
class OrderItem(BaseModel):
    name: str
    quantity: int
    price: float

class CreateOrderRequest(BaseModel):
    customer_id: str
    restaurant_id: str
    items: List[OrderItem]
    delivery_address: Optional[str] = None
    special_instructions: Optional[str] = None

class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    restaurant_id: str
    total: float
    status: str
    payment_status: str
    created_at: str

class UpdateOrderStatusRequest(BaseModel):
    status: int
    notes: Optional[str] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": {
        "order_service": ORDER_SERVICE_ADDRESS,
        "payment_service": PAYMENT_SERVICE_ADDRESS
    }}

if __name__ == "__main__":
    # Get port from environment or use default
    port_env = os.getenv("API_GATEWAY_PORT", "8000")
    try:
        port = int(port_env)
    except ValueError:
        # If the environment variable is not a simple integer, fall back to default
        port = 8000
    # Start server
    uvicorn.run("api_gateway:app", host="0.0.0.0", port=port, reload=False)