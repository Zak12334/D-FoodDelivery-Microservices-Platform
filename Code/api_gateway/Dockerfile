FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy API gateway code
COPY api_gateway.py .

# Expose API port
EXPOSE 8000

# Run the service
CMD ["python", "api_gateway.py"]