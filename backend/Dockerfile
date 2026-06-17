FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl wget unzip docker.io-cli \
    && rm -rf /var/lib/apt/lists/*

# Install nuclei
RUN wget -q --tries=3 --timeout=60 \
    "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip" -O /tmp/nuclei.zip \
    && unzip -q /tmp/nuclei.zip -d /usr/local/bin/ \
    && rm /tmp/nuclei.zip \
    && chmod +x /usr/local/bin/nuclei

# Install dalfox
RUN wget -q --tries=3 --timeout=60 \
    "https://github.com/hahwul/dalfox/releases/latest/download/dalfox_linux_amd64.zip" -O /tmp/dalfox.zip \
    && unzip -q /tmp/dalfox.zip -d /usr/local/bin/ \
    && rm /tmp/dalfox.zip \
    && chmod +x /usr/local/bin/dalfox

# Install ffuf
RUN wget -q --tries=3 --timeout=60 \
    "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_linux_amd64.zip" -O /tmp/ffuf.zip \
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
