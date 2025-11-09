# Use a slim Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY main.py .

# Create the custom downloads directory
RUN mkdir -p /usr/app/downloads/ig && chmod 755 /usr/app/downloads/ig

# Expose port for health checks
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]
