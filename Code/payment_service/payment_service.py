import grpc
import uuid
import datetime
from concurrent import futures
import logging
import time
import random

# Import generated protobuf code
import payment_service_pb2
import payment_service_pb2_grpc
import order_service_pb2
import order_service_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory database for simplicity
transactions_db = {}

class PaymentServicer(payment_service_pb2_grpc.PaymentServiceServicer):
    """Implementation of the Payment Service gRPC service."""
    
    def __init__(self, order_service_address):
        self.order_service_address = order_service_address
    
    def _get_order_stub(self):
        """Create a stub for the Order Service."""
        channel = grpc.insecure_channel(self.order_service_address)
        return order_service_pb2_grpc.OrderServiceStub(channel)
    
    def ProcessPayment(self, request, context):
        """Process a payment for an order."""
        order_id = request.order_id
        amount = request.amount
        payment_method = request.payment_method
        
        logger.info(f"Processing payment of ${amount:.2f} for order {order_id} using {self._get_payment_method_name(payment_method)}")
        
        # Generate a unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Get current timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Simulate payment processing (90% success rate)
        success = random.random() < 0.9
        
        # Determine payment status based on success
        if success:
            status = payment_service_pb2.PAYMENT_COMPLETED
            logger.info(f"Payment for order {order_id} completed successfully")
        else:
            status = payment_service_pb2.PAYMENT_FAILED
            logger.info(f"Payment for order {order_id} failed")
        
        # Create transaction record
        transaction = {
            'transaction_id': transaction_id,
            'order_id': order_id,
            'amount': amount,
            'payment_method': payment_method,
            'status': status,
            'created_at': timestamp
        }
        
        # Store transaction in database
        transactions_db[transaction_id] = transaction
        
        # Notify Order Service about payment status update
        try:
            order_stub = self._get_order_stub()
            update_request = order_service_pb2.UpdatePaymentStatusRequest(
                order_id=order_id,
                payment_status=status
            )
            
            # Call Order Service to update payment status
            order_stub.UpdatePaymentStatus(update_request)
            logger.info(f"Order Service notified about payment status update for order {order_id}")
            
        except Exception as e:
            logger.error(f"Error notifying Order Service: {e}")
        
        # Create response
        return self._create_payment_response(transaction)
    
    def GetTransaction(self, request, context):
        """Get details of a payment transaction."""
        transaction_id = request.transaction_id
        logger.info(f"Getting transaction {transaction_id}")
        
        if transaction_id not in transactions_db:
            context.set_details(f"Transaction {transaction_id} not found")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return payment_service_pb2.PaymentResponse()
        
        transaction = transactions_db[transaction_id]
        return self._create_payment_response(transaction)
    
    def _create_payment_response(self, transaction):
        """Create a PaymentResponse from a transaction dict."""
        return payment_service_pb2.PaymentResponse(
            transaction_id=transaction['transaction_id'],
            order_id=transaction['order_id'],
            amount=transaction['amount'],
            payment_method=transaction['payment_method'],
            status=transaction['status'],
            created_at=transaction['created_at']
        )
    
    def _get_payment_method_name(self, payment_method):
        """Get a human-readable name for a payment method enum value."""
        if payment_method == payment_service_pb2.CREDIT_CARD:
            return "Credit Card"
        elif payment_method == payment_service_pb2.DEBIT_CARD:
            return "Debit Card"
        elif payment_method == payment_service_pb2.DIGITAL_WALLET:
            return "Digital Wallet"
        else:
            return "Unknown Payment Method"

def serve(port, order_service_address):
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_service_pb2_grpc.add_PaymentServiceServicer_to_server(
        PaymentServicer(order_service_address), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"Payment Service started on port {port}")
    logger.info(f"Connected to Order Service at {order_service_address}")
    try:
        while True:
            time.sleep(86400)  # One day in seconds
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Payment Service')
    parser.add_argument('--port', type=int, default=50052,
                        help='Port to listen on')
    parser.add_argument('--order-service', type=str, default='localhost:50051',
                        help='Address of the Order Service')
    
    args = parser.parse_args()
    
    serve(args.port, args.order_service)