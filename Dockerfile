FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Expose port
EXPOSE 8082

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
