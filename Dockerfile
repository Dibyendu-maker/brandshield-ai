FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for OpenCV and document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "run_servers.py"]
