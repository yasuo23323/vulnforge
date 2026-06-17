FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl wget unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI binary (client only, for nuclei Docker mode)
RUN curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-27.5.1.tgz" -o /tmp/docker.tgz \
    && tar xzf /tmp/docker.tgz -C /tmp/ \
    && mv /tmp/docker/docker /usr/local/bin/ \
    && rm -rf /tmp/docker /tmp/docker.tgz

# Install nuclei
RUN curl -Lf "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip" -o /tmp/nuclei.zip \
    && unzip -q /tmp/nuclei.zip -d /usr/local/bin/ \
    && rm /tmp/nuclei.zip \
    && chmod +x /usr/local/bin/nuclei

# Install dalfox
RUN curl -Lf "https://github.com/hahwul/dalfox/releases/latest/download/dalfox_linux_amd64.zip" -o /tmp/dalfox.zip \
    && unzip -q /tmp/dalfox.zip -d /usr/local/bin/ \
    && rm /tmp/dalfox.zip \
    && chmod +x /usr/local/bin/dalfox

# Install ffuf
RUN curl -Lf "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_linux_amd64.zip" -o /tmp/ffuf.zip \
    && unzip -q /tmp/ffuf.zip -d /usr/local/bin/ \
    && rm /tmp/ffuf.zip \
    && chmod +x /usr/local/bin/ffuf

# sqlmap and Python deps
RUN pip install --no-cache-dir sqlmap
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

