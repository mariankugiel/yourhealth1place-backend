#!/bin/bash

# Update system
yum update -y

# Install required packages
yum install -y python3 python3-pip git nginx postgresql15

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /opt/yourhealth1place
cd /opt/yourhealth1place

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=${AWS_REGION}
      - AWS_S3_BUCKET=${AWS_S3_BUCKET}
      - DATABASE_URL=${DATABASE_URL}
      - AKEYLESS_ACCESS_ID=${AKEYLESS_ACCESS_ID}
      - AKEYLESS_ACCESS_KEY=${AKEYLESS_ACCESS_KEY}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
    restart: unless-stopped
EOF

# Create nginx configuration
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
boto3==1.34.0
aioboto3==12.3.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
alembic==1.13.1
redis==5.0.1
requests==2.31.0
EOF

# Create application structure
mkdir -p app/{api/v1/endpoints,core,crud,models,schemas}

# Create main application file
cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "YourHealth1Place API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
EOF

# Create config file
cat > app/core/config.py << 'EOF'
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    
    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    AWS_S3_BUCKET: str = ""
    
    # Akeyless
    AKEYLESS_ACCESS_ID: str = ""
    AKEYLESS_ACCESS_KEY: str = ""
    
    # Application
    PROJECT_NAME: str = "YourHealth1Place API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()
EOF

# Create __init__.py files
touch app/__init__.py
touch app/core/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/crud/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py

# Set permissions
chmod +x /opt/yourhealth1place/docker-compose.yml

# Start the application
cd /opt/yourhealth1place
docker-compose up -d

# Create systemd service for auto-restart
cat > /etc/systemd/system/yourhealth1place.service << 'EOF'
[Unit]
Description=YourHealth1Place Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/yourhealth1place
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl enable yourhealth1place.service
systemctl start yourhealth1place.service

# Create log directory
mkdir -p /var/log/yourhealth1place
chown -R ec2-user:ec2-user /var/log/yourhealth1place

echo "YourHealth1Place application setup completed!" 