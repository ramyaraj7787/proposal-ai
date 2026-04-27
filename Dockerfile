FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for FAISS or doc parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging configuration first (for caching)
COPY pyproject.toml .

# Install dependencies (upgrade pip first)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

# Copy the rest of the application
COPY . .

# Expose the default Streamlit port
EXPOSE 8501

# Run the Streamlit app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
