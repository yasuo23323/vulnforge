# VulnForge

AI-enhanced web vulnerability scanner. Scans targets with 4 security tools (nuclei, sqlmap, dalfox, ffuf), then automatically analyzes each finding with LLM (DeepSeek/OpenAI) using 3 prompting strategies to identify false positives.

## Quick Start

```bash
git clone https://github.com/yasuo23323/vulnforge.git
cd vulnforge
bash final_version/start.sh
```

Enter your DeepSeek/OpenAI API key when prompted. Open the browser URL shown.

## Usage

1. Open `http://YOUR_SERVER_IP:3000` in your browser
2. Click "New Scan"
3. Enter target URL (e.g. `http://192.168.1.100:8080`)
4. Select scanners (recommend: all 4)
5. Click "Scan"
6. Wait for completion (2-5 min)
7. View findings with LLM analysis (Zero-shot, Few-shot, Chain-of-Thought)

## Architecture

- **Backend**: Python FastAPI + SQLAlchemy (PostgreSQL)
- **Frontend**: React + TypeScript + Ant Design
- **Scanners**: nuclei (Docker), sqlmap (pip), dalfox (Docker), ffuf (binary)
- **LLM**: DeepSeek Chat / OpenAI GPT (configurable)
- **Deployment**: Docker Compose

## Requirements

- Linux (tested on Kali, Ubuntu 22.04+)
- Docker Engine 24+ and Docker Compose v2
- DeepSeek or OpenAI API key
- 8GB+ RAM recommended

## Project Structure

```
vulnforge/
??? backend/          # Python FastAPI backend
??? frontend/         # React TypeScript frontend
??? final_version/    # Deployment files
?   ??? docker-compose.yml
?   ??? start.sh
?   ??? .env.example
??? .gitattributes    # LF line endings enforcement
```
