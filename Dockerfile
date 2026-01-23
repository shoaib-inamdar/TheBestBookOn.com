FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application files
COPY main.py .
COPY populate_db.py .
COPY patch_db.py .
COPY thebestbookon_seed.db .

# Copy static and templates directories
COPY static/ ./static/
COPY templates/ ./templates/

# Copy seed database to working database
RUN cp thebestbookon_seed.db thebestbookon.db

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
