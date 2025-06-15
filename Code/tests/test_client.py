import grpc
import argparse
import uuid

# Import generated protobuf code
import order_service_pb2
import order_service_pb2_grpc
import payment_service_pb2
import payment_service_pb2_grpc

def test_order_creation(order_stub):
    """Test creating a new order."""
    print("\n Testing Order Creation ")
    
    # Create order items
    items = [
        order_service_pb2.OrderItem(
            name="Margherita Pizza",
            quantity=2,
            price=12.99
        ),
        order_service_pb2.OrderItem(
            name="Garlic Bread",
            quantity=1,
            price=4.99
        )
    ]
    
    # Create order request
    customer_id = f"cust-{uuid.uuid4().hex[:8]}"
    restaurant_id = "rest-123"
    
    request = order_service_pb2.CreateOrderRequest(
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        items=items
    )
    
    # Call service
    try:
        response = order_stub.CreateOrder(request)
        print(f"Order created successfully!")
        print(f"Order ID: {response.order_id}")
        print(f"Total: ${response.total:.2f}")
        print(f"Status: {get_order_status_name(response.status)}")
        print(f"Payment Status: {get_payment_status_name(response.payment_status)}")
        
        # Return order ID for further testing
        return response.order_id
    
    except grpc.RpcError as e:
        print(f"Error creating order: {e.details()}")
        return None

def test_get_order(order_stub, order_id):
    """Test getting order details."""
    print("\n Testing Get Order ")
    
    request = order_service_pb2.GetOrderRequest(order_id=order_id)
    
    try:
        response = order_stub.GetOrder(request)
        print(f"Order details retrieved:")
        print(f"Order ID: {response.order_id}")
        print(f"Customer ID: {response.customer_id}")
        print(f"Restaurant ID: {response.restaurant_id}")
        print(f"Status: {get_order_status_name(response.status)}")
        print(f"Payment Status: {get_payment_status_name(response.payment_status)}")
        print(f"Items:")
        for item in response.items:
            print(f"  - {item.name} x{item.quantity}: ${item.price:.2f}")
        print(f"Total: ${response.total:.2f}")
        
        return response
    
    except grpc.RpcError as e:
        print(f"Error getting order: {e.details()}")
        return None

def test_update_order_status(order_stub, order_id):
    """Test updating order status."""
    print("\n Testing Update Order Status ")
    
    request = order_service_pb2.UpdateOrderStatusRequest(
        order_id=order_id,
        status=order_service_pb2.ORDER_PREPARING
    )
    
    try:
        response = order_stub.UpdateOrderStatus(request)
        print(f"Order status updated:")
        print(f"Order ID: {response.order_id}")
        print(f"New Status: {get_order_status_name(response.status)}")
        return response
    
    except grpc.RpcError as e:
        print(f"Error updating order status: {e.details()}")
        return None

def test_get_transaction(payment_stub, order):
    """Test getting transaction details."""
    if not order.transaction_id:
        print("No transaction ID available")
        return None
        
    print("\n Testing Get Transaction ")
    
    request = payment_service_pb2.GetTransactionRequest(transaction_id=order.transaction_id)
    
    try:
        response = payment_stub.GetTransaction(request)
        print(f"Transaction details retrieved:")
        print(f"Transaction ID: {response.transaction_id}")
        print(f"Order ID: {response.order_id}")
        print(f"Amount: ${response.amount:.2f}")
        print(f"Status: {get_payment_status_name(response.status)}")
        
        return response
    
    except grpc.RpcError as e:
        print(f"Error getting transaction: {e.details()}")
        return None

def get_order_status_name(status):
    """Convert order status enum to human-readable name."""
    status_names = {
        order_service_pb2.ORDER_PENDING: "Pending",
        order_service_pb2.ORDER_CONFIRMED: "Confirmed",
        order_service_pb2.ORDER_PREPARING: "Preparing",
        order_service_pb2.ORDER_READY_FOR_PICKUP: "Ready for Pickup",
        order_service_pb2.ORDER_OUT_FOR_DELIVERY: "Out for Delivery",
        order_service_pb2.ORDER_DELIVERED: "Delivered",
        order_service_pb2.ORDER_CANCELLED: "Cancelled"
    }
    return status_names.get(status, f"Unknown Status ({status})")

def get_payment_status_name(status):
    """Convert payment status enum to human-readable name."""
    status_names = {
        payment_service_pb2.PAYMENT_PENDING: "Pending",
        payment_service_pb2.PAYMENT_PROCESSING: "Processing",
        payment_service_pb2.PAYMENT_COMPLETED: "Completed",
        payment_service_pb2.PAYMENT_FAILED: "Failed",
        payment_service_pb2.PAYMENT_REFUNDED: "Refunded"
    }
    return status_names.get(status, f"Unknown Status ({status})")

def run_tests(order_service_address, payment_service_address):
    """Run a series of tests for the Order and Payment services."""
    # Create stubs for both services
    order_channel = grpc.insecure_channel(order_service_address)
    order_stub = order_service_pb2_grpc.OrderServiceStub(order_channel)
    
    payment_channel = grpc.insecure_channel(payment_service_address)
    payment_stub = payment_service_pb2_grpc.PaymentServiceStub(payment_channel)
    
    print(" Starting Microservices Test Suite ")
    print(f"Order Service: {order_service_address}")
    print(f"Payment Service: {payment_service_address}")
    
    # Test 1: Create a new order
    order_id = test_order_creation(order_stub)
    if not order_id:
        print("Order creation failed. Exiting tests.")
        return
    
    # Test 2: Get order details
    order = test_get_order(order_stub, order_id)
    if not order:
        print("Get order failed. Continuing with other tests.")
    
    # Test 3: Update order status
    updated_order = test_update_order_status(order_stub, order_id)
    
    # Test 4: Get transaction details (if available)
    if order:
        transaction = test_get_transaction(payment_stub, order)
    
    print("\n Test Suite Completed ")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Microservices Test Client')
    parser.add_argument('--order-service', type=str, default='localhost:50051',
                        help='Address of the Order Service')
    parser.add_argument('--payment-service', type=str, default='localhost:50052',
                        help='Address of the Payment Service')
    
    args = parser.parse_args()
    
    run_tests(args.order_service, args.payment_service)