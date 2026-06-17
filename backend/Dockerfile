FROM python:3.12-slim

WORKDIR /app

# Install system dependencies + scanner tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install nuclei (Go-based vulnerability scanner)
RUN wget -q https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip \
    && unzip -q nuclei_linux_amd64.zip -d /usr/local/bin/ \
    && rm nuclei_linux_amd64.zip \
    && chmod +x /usr/local/bin/nuclei

# Install dalfox (XSS scanner)
RUN wget -q https://github.com/hahwul/dalfox/releases/latest/download/dalfox_linux_amd64.zip \
    && unzip -q dalfox_linux_amd64.zip -d /usr/local/bin/ \
    && rm dalfox_linux_amd64.zip \
    && chmod +x /usr/local/bin/dalfox

# Install ffuf (directory fuzzer)
RUN wget -q https://github.com/ffuf/ffuf/releases/latest/download/ffuf_linux_amd64.zip \
    && unzip -q ffuf_linux_amd64.zip -d /usr/local/bin/ \
    && rm ffuf_linux_amd64.zip \
    && chmod +x /usr/local/bin/ffuf

# sqlmap is Python-native, install via pip
RUN pip install --no-cache-dir sqlmap

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
