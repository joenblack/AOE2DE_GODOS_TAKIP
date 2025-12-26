FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (if we had them separate, for now we can install directly or create requirements.txt)
# Let's create a requirements.txt on the fly or copy it if it exists.
# For this step, I will write the requirements file in the next step, so here I assume it exists.
COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entrypoint is defined in docker-compose
