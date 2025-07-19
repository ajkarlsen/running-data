# Use an official Python base image suitable for ARM (Raspberry Pi)
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy your requirements file first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app files
COPY . .

# Expose the default Streamlit port
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
