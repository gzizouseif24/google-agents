FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the port that ADK will use
EXPOSE 8000

# Command to run the application
CMD ["adk", "web", "--port", "8000"] 