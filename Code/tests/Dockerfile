FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY test_client.py .
COPY protos/ ./protos/

# Generate proto files with the updated path
RUN python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/order_service.proto
RUN python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/payment_service.proto

CMD ["python", "test_client.py"]