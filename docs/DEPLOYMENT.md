# Deployment Guide

This guide covers deploying the XRPL Offline Payments system for production use.

## Table of Contents

1. [Quick Start (Docker)](#quick-start-docker)
2. [Production Deployment](#production-deployment)
3. [Environment Configuration](#environment-configuration)
4. [Security Hardening](#security-hardening)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup & Recovery](#backup--recovery)
7. [Scaling](#scaling)
8. [Troubleshooting](#troubleshooting)

## Quick Start (Docker)

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-org/xrpl-offline-payments.git
cd xrpl-offline-payments

# Copy environment file
cp .env.example .env

# Generate merchant wallet (CRITICAL!)
cd tools
python generate_merchant_wallet.py
# Copy the generated seed to .env as MERCHANT_SEED

# Edit .env and configure:
nano .env
# - Set MERCHANT_SEED (from above)
# - Set JWT_SECRET (generate random 64-char string)
# - Set DEV_NO_AUTH=false for production
# - Set DEV_SIMULATE_SETTLEMENT=false for live settlements
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Verify Deployment

```bash
# Check API health
curl http://localhost/health | jq

# Expected output:
# {
#   "ok": true,
#   "db": "connected",
#   "merchant_address": "rYourMerchantAddress..."
# }

# Access web dashboard
open http://localhost
```

### 4. Run Demo Setup

```bash
# Initialize with demo data
bash scripts/demo-setup.sh
```

## Production Deployment

### Architecture Overview

```
┌─────────────────┐
│   Nginx (80)    │  ← Reverse Proxy + SSL
└────────┬────────┘
         │
    ┌────┴────┬──────────┐
    │         │          │
┌───▼────┐ ┌──▼──────┐ ┌▼────────┐
│Frontend│ │   API   │ │ MongoDB │
│ (3001) │ │ (3000)  │ │ (27017) │
└────────┘ └─────┬───┘ └─────────┘
                 │
             ┌───▼───┐
             │ Redis │
             │(6379) │
             └───────┘
```

### Cloud Deployment Options

#### Option 1: AWS EC2

1. **Launch EC2 Instance**
   - Instance type: t3.medium (minimum)
   - OS: Ubuntu 22.04 LTS
   - Storage: 20GB SSD
   - Security Group: Allow 80, 443, 22

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose git
   sudo systemctl enable docker
   sudo usermod -aG docker $USER
   ```

3. **Deploy Application**
   ```bash
   git clone <your-repo>
   cd xrpl-offline-payments
   cp .env.example .env
   # Configure .env
   docker-compose up -d
   ```

4. **Configure DNS**
   - Point domain to EC2 public IP
   - Update nginx config with domain name

5. **Setup SSL (Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d xacceptapay.com -d www.xacceptapay.com
   ```

#### Option 2: DigitalOcean Droplet

1. **Create Droplet**
   - Size: 2 GB RAM / 1 vCPU ($12/mo)
   - Image: Docker on Ubuntu 22.04
   - Datacenter: Choose closest to customers

2. **Deploy via SSH**
   ```bash
   ssh root@your-droplet-ip
   git clone <your-repo>
   cd xrpl-offline-payments
   # Configure and start
   docker-compose up -d
   ```

3. **Add Domain**
   - Configure DNS in DigitalOcean dashboard
   - Setup SSL with certbot (same as AWS)

#### Option 3: Kubernetes (Scale)

See [docs/KUBERNETES.md](./KUBERNETES.md) for k8s deployment

### Environment Configuration

#### Critical Settings for Production

```bash
# .env for production

# Security
NODE_ENV=production
DEV_NO_AUTH=false  # CRITICAL: Enable auth!
JWT_SECRET=<64-char-random-string>
MERCHANT_SEED=<your-testnet-or-mainnet-seed>

# Network (choose ONE)
# Testnet for pilots:
RPC_URL=wss://s.altnet.rippletest.net:51233

# Mainnet for production:
# RPC_URL=wss://xrplcluster.com

# Operation
DEV_SIMULATE_SETTLEMENT=false  # Real XRPL submissions
EXPOSURE_CAP_DROPS=5000000     # 5 XRP max unsettled

# Database
USE_DB=true
MONGODB_URI=mongodb://admin:<strong-password>@mongodb:27017/xcceptapay?authSource=admin

# Rate limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
```

#### Generating Secrets

```bash
# JWT Secret (64 characters)
openssl rand -hex 32

# MongoDB Password
openssl rand -base64 32

# Merchant Seed (XRPL)
cd tools && python generate_merchant_wallet.py
```

## Security Hardening

### 1. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 2. SSL/TLS Setup

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d xacceptapay.com

# Auto-renewal (already setup by certbot)
sudo certbot renew --dry-run
```

### 3. Nginx Security Headers

Add to `nginx/conf.d/default.conf`:

```nginx
# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

### 4. Database Security

```bash
# Change default MongoDB password
docker-compose exec mongodb mongo -u admin -p

> use admin
> db.changeUserPassword("admin", "new-strong-password")

# Update docker-compose.yml and .env with new password
```

### 5. Secrets Management

**For production, use:**
- AWS Secrets Manager
- HashiCorp Vault
- Docker Secrets (Swarm mode)

Example with Docker Secrets:
```bash
echo "your-merchant-seed" | docker secret create merchant_seed -
echo "your-jwt-secret" | docker secret create jwt_secret -
```

## Monitoring & Logging

### 1. Application Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api

# Export logs
docker-compose logs --no-color > app-logs-$(date +%Y%m%d).log
```

### 2. Log Aggregation (ELK Stack)

Add to `docker-compose.yml`:

```yaml
elasticsearch:
  image: elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data

kibana:
  image: kibana:8.11.0
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch

logstash:
  image: logstash:8.11.0
  volumes:
    - ./logstash/pipeline:/usr/share/logstash/pipeline
  depends_on:
    - elasticsearch
```

### 3. Metrics (Prometheus + Grafana)

See [docs/MONITORING.md](./MONITORING.md) for full setup

### 4. Uptime Monitoring

Recommended services:
- UptimeRobot (free tier available)
- Pingdom
- StatusCake

Monitor endpoints:
- `https://xacceptapay.com/health`
- `https://xacceptapay.com/api/health`

## Backup & Recovery

### 1. MongoDB Backup

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR=/backups/mongodb
DATE=$(date +%Y%m%d_%H%M%S)

docker-compose exec -T mongodb mongodump \
  --username admin \
  --password $MONGO_PASSWORD \
  --authenticationDatabase admin \
  --db xcceptapay \
  --archive | gzip > $BACKUP_DIR/xcceptapay_$DATE.archive.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.archive.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup-script.sh
```

### 2. Restore from Backup

```bash
# Restore MongoDB
gunzip < xcceptapay_20240101_020000.archive.gz | \
docker-compose exec -T mongodb mongorestore \
  --username admin \
  --password $MONGO_PASSWORD \
  --authenticationDatabase admin \
  --archive
```

### 3. Disaster Recovery Plan

1. **Backup Merchant Seed** (offline, encrypted storage)
2. **Daily database backups** (automated)
3. **Configuration files** (version controlled)
4. **Infrastructure as Code** (docker-compose.yml, nginx configs)

Recovery Time Objective (RTO): < 1 hour
Recovery Point Objective (RPO): < 24 hours

## Scaling

### Horizontal Scaling (Multiple API Instances)

```yaml
# docker-compose.yml
api:
  deploy:
    replicas: 3
  # ... rest of config

nginx:
  # Update upstream to load balance
```

### Vertical Scaling (Resource Limits)

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

### Database Scaling

- Enable MongoDB replica set
- Add read replicas for queries
- Implement sharding for high volume

## Troubleshooting

### Common Issues

#### 1. API Returns 502

```bash
# Check API container status
docker-compose ps api

# View API logs
docker-compose logs api

# Restart API
docker-compose restart api
```

#### 2. Database Connection Failed

```bash
# Check MongoDB status
docker-compose ps mongodb

# Verify credentials in .env
# Test connection
docker-compose exec mongodb mongo \
  -u admin -p $MONGO_PASSWORD --authenticationDatabase admin
```

#### 3. Frontend Not Loading

```bash
# Check nginx logs
docker-compose logs nginx

# Verify build
docker-compose exec frontend ls -la /usr/share/nginx/html

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

#### 4. XRPL Connection Issues

```bash
# Test RPC connection
curl -X POST https://s.altnet.rippletest.net:51234 \
  -H "Content-Type: application/json" \
  -d '{"method": "server_info"}'

# Try alternative RPC
# Edit .env: RPC_URL=wss://s.devnet.rippletest.net:51233
```

### Health Checks

```bash
# API health
curl http://localhost:3000/health | jq

# Database health
docker-compose exec mongodb mongo --eval "db.adminCommand('ping')"

# Redis health
docker-compose exec redis redis-cli ping
```

### Performance Tuning

```bash
# Monitor container resources
docker stats

# MongoDB slow queries
docker-compose exec mongodb mongo xcceptapay \
  --eval "db.setProfilingLevel(1, 100)"
```

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Apply updates (zero-downtime)
docker-compose up -d --no-deps --build api
docker-compose up -d --no-deps --build frontend
```

### Database Migrations

```bash
# Run migration scripts
docker-compose exec api node scripts/migrate.js
```

## Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Review [docs/TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
3. Open issue on GitHub
4. Contact: support@xacceptapay.com

## License

MIT
