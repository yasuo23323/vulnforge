FROM python:3.12-slim

WORKDIR /app

# Install system dependencies + scanner tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set pip to use Tsinghua mirror (China-friendly)
ENV PIP_INDEX_URL=https://pypi.org/simple

# Install nuclei via ghproxy (GitHub mirror for China)
RUN curl -sL -o nuclei.zip "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip" \
    && unzip -q nuclei.zip -d /usr/local/bin/ \
    && rm nuclei.zip \
    && chmod +x /usr/local/bin/nuclei

# Install dalfox via ghproxy
RUN curl -sL -o dalfox.zip "https://github.com/hahwul/dalfox/releases/latest/download/dalfox_linux_amd64.zip" \
    && unzip -q dalfox.zip -d /usr/local/bin/ \
    && rm dalfox.zip \
    && chmod +x /usr/local/bin/dalfox

# Install ffuf via ghproxy
RUN curl -sL -o ffuf.zip "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_linux_amd64.zip" \
    && unzip -q ffuf.zip -d /usr/local/bin/ \
    && rm ffuf.zip \
    && chmod +x /usr/local/bin/ffuf

# sqlmap via pip (uses Tsinghua mirror)
RUN pip install --no-cache-dir sqlmap

# Install Python dependencies (uses Tsinghua mirror)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
