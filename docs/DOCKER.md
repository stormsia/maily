# Docker & Installation Guide

Run Maily via official pre-built Docker containers, Docker Compose, or develop locally from source.

### Option A — Docker (Pre-built Image, No Git Clone Required)

The fastest and recommended way to run **maily** in production without cloning the repository or building from source:

#### 1. In One Command (`docker run`)

```bash
docker run -d \
  --name maily \
  -p 8477:8477 \
  -e MAILY_API_KEY=your_secret_api_key \
  -v maily_data:/data \
  --restart unless-stopped \
  ghcr.io/stormsia/maily:latest
```

#### 2. Using Docker Compose

Download only the production Compose configuration:

```bash
# Linux / macOS (curl)
curl -O https://raw.githubusercontent.com/stormsia/maily/main/docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d

# Windows (PowerShell)
Invoke-WebRequest -Uri https://raw.githubusercontent.com/stormsia/maily/main/docker-compose.prod.yml -OutFile docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

#### Updating the Pre-built Image

```bash
# If using Docker Compose:
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# If using docker run:
docker pull ghcr.io/stormsia/maily:latest
docker stop maily && docker rm maily
docker run -d --name maily -p 8477:8477 -e MAILY_API_KEY=your_secret_api_key -v maily_data:/data --restart unless-stopped ghcr.io/stormsia/maily:latest
```

- Web Dashboard: <http://127.0.0.1:8477/>
- API Documentation: <http://127.0.0.1:8477/docs>

---

### Option B — Build from Source / Development

#### 1. Docker Compose (Local Build)

```bash
git clone https://github.com/stormsia/maily.git && cd maily
cp .env.example .env        # adjust if needed
docker compose up -d --build
```

To update when building from source:
```bash
git pull
docker compose up -d --build
```

#### 2. Local Python (Python 3.13+)

##### From PyPI (Recommended for Python CLI)

```bash
pip install maily-server
maily
```

##### From Git Source (Development)

```bash
git clone https://github.com/stormsia/maily.git && cd maily
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -e ".[dev]"
maily
```

Development server with auto-reload:
```bash
uvicorn maily.app.main:create_app --factory --reload --port 8477
```
