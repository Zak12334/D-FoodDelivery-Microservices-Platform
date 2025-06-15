import requests
import json
import time
import argparse

def test_api_gateway(base_url):
    """Test the API Gateway endpoints."""
    
    print(" Testing API Gateway ")
    
    # Wait for services to be ready
    print("Waiting for services to be ready...")
    time.sleep(2)
    
    # Test health check
    print("\n1. Testing health check endpoint")
    response = requests.get(f"{base_url}/health")
    if response.status_code == 200:
        print("Health check successful!")
        print(f"Services: {json.dumps(response.json()['services'], indent=2)}")
    else:
        print(f"Health check failed with status code {response.status_code}")
        print(response.text)
        return
    
    # Test creating an order
    print("\n2. Testing order creation")
    order_data = {
        "customer_id": "cust-test-123",
        "restaurant_id": "rest-test-456",
        "items": [
            {
                "name": "Test Pizza",
                "quantity": 2,
                "price": 12.99
            },
            {
                "name": "Test Soda",
                "quantity": 1,
                "price": 2.99
            }
        ],
        "delivery_address": "123 Test St, Test City",
        "special_instructions": "Ring the doorbell"
    }
    
    response = requests.post(f"{base_url}/orders", json=order_data)
    if response.status_code == 200:
        order = response.json()
        order_id = order["order_id"]
        print("Order created successfully!")
        print(f"Order ID: {order_id}")
        print(f"Total: ${order['total']:.2f}")
        print(f"Status: {order['status']}")
        print(f"Payment Status: {order['payment_status']}")
    else:
        print(f"Order creation failed with status code {response.status_code}")
        print(response.text)
        return
    
    # Test getting order details
    print("\n3. Testing get order endpoint")
    response = requests.get(f"{base_url}/orders/{order_id}")
    if response.status_code == 200:
        order = response.json()
        print("Order retrieved successfully!")
        print(f"Order ID: {order['order_id']}")
        print(f"Customer ID: {order['customer_id']}")
        print(f"Restaurant ID: {order['restaurant_id']}")
        print(f"Total: ${order['total']:.2f}")
        print(f"Status: {order['status']}")
        print(f"Payment Status: {order['payment_status']}")
    else:
        print(f"Get order failed with status code {response.status_code}")
        print(response.text)
    
    # Test updating order status
    print("\n4. Testing update order status endpoint")
    status_data = {
        "status": 2,  # Preparing
        "notes": "Kitchen has started preparing the order"
    }
    
    response = requests.put(f"{base_url}/orders/{order_id}/status", json=status_data)
    if response.status_code == 200:
        order = response.json()
        print("Order status updated successfully!")
        print(f"Order ID: {order['order_id']}")
        print(f"New Status: {order['status']}")
    else:
        print(f"Update order status failed with status code {response.status_code}")
        print(response.text)
    
    print("\n API Gateway Test Completed ")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test the API Gateway')
    parser.add_argument('--base-url', type=str, default='http://localhost:8000',
                        help='Base URL of the API Gateway')
    
    args = parser.parse_args()
    
    test_api_gateway(args.base_url)