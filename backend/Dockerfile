FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl wget unzip \
    && rm -rf /var/lib/apt/lists/*

# Install nuclei (best-effort, falls back to Docker mode)
RUN wget -q --tries=3 --timeout=30 \
    "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip" -O nuclei.zip \
    && unzip -q nuclei.zip -d /usr/local/bin/ \
    && rm nuclei.zip \
    && chmod +x /usr/local/bin/nuclei || echo "[WARN] nuclei download failed, will use Docker mode"

# Install dalfox
RUN wget -q --tries=3 --timeout=30 \
    "https://github.com/hahwul/dalfox/releases/latest/download/dalfox_linux_amd64.zip" -O dalfox.zip \
    && unzip -q dalfox.zip -d /usr/local/bin/ \
    && rm dalfox.zip \
    && chmod +x /usr/local/bin/dalfox || echo "[WARN] dalfox download failed"

# Install ffuf
RUN wget -q --tries=3 --timeout=30 \
    "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_linux_amd64.zip" -O ffuf.zip \
    && unzip -q ffuf.zip -d /usr/local/bin/ \
    && rm ffuf.zip \
    && chmod +x /usr/local/bin/ffuf || echo "[WARN] ffuf download failed"

# sqlmap and Python deps
RUN pip install --no-cache-dir sqlmap
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
