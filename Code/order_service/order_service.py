import grpc
import uuid
import datetime
from concurrent import futures
import logging
import time

# Import generated protobuf code
import order_service_pb2
import order_service_pb2_grpc
import payment_service_pb2
import payment_service_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory database for simplicity
orders_db = {}

class OrderServicer(order_service_pb2_grpc.OrderServiceServicer):
    """Implementation of the Order Service gRPC service."""
    
    def __init__(self, payment_service_address):
        self.payment_service_address = payment_service_address
    
    def _get_payment_stub(self):
        """Create a stub for the Payment Service."""
        channel = grpc.insecure_channel(self.payment_service_address)
        return payment_service_pb2_grpc.PaymentServiceStub(channel)
    
    def CreateOrder(self, request, context):
        """Create a new order with the provided details."""
        logger.info(f"Creating new order for customer {request.customer_id}")
        
        # Generate a unique order ID
        order_id = str(uuid.uuid4())
        
        # Calculate total from items
        total = sum(item.price * item.quantity for item in request.items)
        
        # Get current timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Create order object
        order = {
            'order_id': order_id,
            'customer_id': request.customer_id,
            'restaurant_id': request.restaurant_id,
            'items': [
                {
                    'name': item.name,
                    'quantity': item.quantity,
                    'price': item.price
                } for item in request.items
            ],
            'total': total,
            'status': order_service_pb2.ORDER_PENDING,
            'payment_status': payment_service_pb2.PAYMENT_PENDING,
            'created_at': timestamp
        }
        
        # Store order in database
        orders_db[order_id] = order
        
        logger.info(f"Created order {order_id} with total ${total:.2f}")
        
        # Process payment
        try:
            payment_stub = self._get_payment_stub()
            payment_request = payment_service_pb2.ProcessPaymentRequest(
                order_id=order_id,
                amount=total,
                payment_method=payment_service_pb2.CREDIT_CARD
            )
            
            # Call payment service to process the payment
            payment_response = payment_stub.ProcessPayment(payment_request)
            
            # Update order with payment information
            order['payment_status'] = payment_response.status
            
            # Update order status based on payment result
            if payment_response.status == payment_service_pb2.PAYMENT_COMPLETED:
                order['status'] = order_service_pb2.ORDER_CONFIRMED
            
            logger.info(f"Payment for order {order_id} processed with status: {payment_response.status}")
            
        except Exception as e:
            logger.error(f"Payment service error: {e}")
            context.set_details(f"Payment service error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return order_service_pb2.OrderResponse()
        
        # Create response
        return self._create_order_response(order)
    
    def GetOrder(self, request, context):
        """Get order details by ID."""
        order_id = request.order_id
        logger.info(f"Getting order {order_id}")
        
        if order_id not in orders_db:
            context.set_details(f"Order {order_id} not found")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return order_service_pb2.OrderResponse()
        
        order = orders_db[order_id]
        return self._create_order_response(order)
    
    def UpdateOrderStatus(self, request, context):
        """Update the status of an order."""
        order_id = request.order_id
        new_status = request.status
        
        logger.info(f"Updating order {order_id} status to {new_status}")
        
        if order_id not in orders_db:
            context.set_details(f"Order {order_id} not found")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return order_service_pb2.OrderResponse()
        
        order = orders_db[order_id]
        
        # Update status
        order['status'] = new_status
        
        logger.info(f"Order {order_id} status updated to {new_status}")
        
        return self._create_order_response(order)
    
    def UpdatePaymentStatus(self, request, context):
        """Update the payment status for an order. Called by the Payment Service."""
        order_id = request.order_id
        payment_status = request.payment_status
        
        logger.info(f"Updating payment status for order {order_id} to {payment_status}")
        
        if order_id not in orders_db:
            context.set_details(f"Order {order_id} not found")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return order_service_pb2.OrderResponse()
        
        order = orders_db[order_id]
        
        # Update payment status
        order['payment_status'] = payment_status
        
        logger.info(f"Order {order_id} payment status updated to {payment_status}")
        
        return self._create_order_response(order)
    
    def _create_order_response(self, order):
        """Create an OrderResponse from an order dict."""
        # Create OrderItem messages
        order_items = []
        for item in order['items']:
            order_item = order_service_pb2.OrderItem(
                name=item['name'],
                quantity=item['quantity'],
                price=item['price']
            )
            order_items.append(order_item)
        
        # Create and return OrderResponse
        return order_service_pb2.OrderResponse(
            order_id=order['order_id'],
            customer_id=order['customer_id'],
            restaurant_id=order['restaurant_id'],
            items=order_items,
            total=order['total'],
            status=order['status'],
            payment_status=order['payment_status'],
            created_at=order['created_at']
        )

def serve(port, payment_service_address):
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_service_pb2_grpc.add_OrderServiceServicer_to_server(
        OrderServicer(payment_service_address), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"Order Service started on port {port}")
    logger.info(f"Connected to Payment Service at {payment_service_address}")
    try:
        while True:
            time.sleep(86400)  # One day in seconds
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Order Service')
    parser.add_argument('--port', type=int, default=50051,
                        help='Port to listen on')
    parser.add_argument('--payment-service', type=str, default='localhost:50052',
                        help='Address of the Payment Service')
    
    args = parser.parse_args()
    
    serve(args.port, args.payment_service)