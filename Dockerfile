# Base image with Python
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies, including tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt and install dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files to the container
COPY . .

# Expose the port that Streamlit will run on
EXPOSE 8501

# Set environment variables to avoid Streamlit asking questions when starting
ENV STREAMLIT_SERVER_HEADLESS true
ENV STREAMLIT_SERVER_PORT 8501

# Run the Streamlit app
CMD ["streamlit", "run", "main.py"]
