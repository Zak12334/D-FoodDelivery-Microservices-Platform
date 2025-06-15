FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY payment_service.py .
COPY protos/order_service.proto .
COPY protos/payment_service.proto .

# Pre-generate the proto modules
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. order_service.proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. payment_service.proto

CMD ["python", "payment_service.py"]