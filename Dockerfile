FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create templates directory
RUN mkdir -p templates

# Expose the port that FastAPI will use
EXPOSE 8001

# Command to run the FastAPI application
CMD ["python", "agent_server.py"] 