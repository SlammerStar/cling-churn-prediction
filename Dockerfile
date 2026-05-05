FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install gunicorn for production serving
RUN pip install gunicorn

# Copy project files
COPY . .

# Expose port
EXPOSE 5002

# We need a simple entrypoint to serve all API endpoints locally.
# We can use gunicorn to serve a simple WSGI app that routes to the correct module.
# For simplicity, we can create a local_app.py that combines them.
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "local_app:app"]
