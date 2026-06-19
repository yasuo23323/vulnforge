FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Install ffuf binary (Docker image not available)
RUN curl -Lf "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_linux_amd64.tar.gz" -o /tmp/ffuf.tar.gz \
    && tar xzf /tmp/ffuf.tar.gz -C /usr/local/bin/ ffuf \
    && rm /tmp/ffuf.tar.gz \
    && chmod +x /usr/local/bin/ffuf || echo "[WARN] ffuf download failed"

# Install Docker CLI binary (for running scanner tools in Docker containers)
RUN curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-27.5.1.tgz" -o /tmp/docker.tgz \
    && tar xzf /tmp/docker.tgz -C /tmp/ \
    && mv /tmp/docker/docker /usr/local/bin/ \
    && rm -rf /tmp/docker /tmp/docker.tgz

# sqlmap and Python deps
RUN pip install --no-cache-dir sqlmap
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

