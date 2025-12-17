FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Installa Docker CLI
RUN curl -fsSL https://get.docker.com/builds/Linux/x86_64/docker-latest.tgz | \
    tar -xzC /usr/local/bin --strip=1 docker/docker

COPY supervisor.py /app/

CMD ["python", "supervisor.py"]
