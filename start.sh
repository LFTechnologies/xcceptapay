#!/bin/bash

# XcceptaPay - One-Command Startup Script
# This script checks prerequisites and starts the entire system

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════╗"
echo "║   XcceptaPay - XRPL Offline Payments ║"
echo "║          Production Startup           ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
echo -e "${BLUE}[1/5]${NC} Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗${NC} Docker not found. Please install Docker first."
    echo "  https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker installed: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗${NC} Docker Compose not found. Please install Docker Compose."
    echo "  https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker Compose installed: $(docker-compose --version)"

# Check .env file
echo ""
echo -e "${BLUE}[2/5]${NC} Checking configuration..."

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠${NC} .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠${NC} IMPORTANT: Edit .env and set:"
    echo "  1. MERCHANT_SEED (generate with: cd tools && python generate_merchant_wallet.py)"
    echo "  2. JWT_SECRET (random 64-char string)"
    echo ""
    read -p "Press Enter when ready to continue, or Ctrl+C to exit and configure..."
else
    echo -e "${GREEN}✓${NC} .env file found"
fi

# Check merchant seed
MERCHANT_SEED=$(grep MERCHANT_SEED .env | cut -d'=' -f2)
if [ "$MERCHANT_SEED" == "sEdVqH1234567890abcdefghijk" ]; then
    echo -e "${YELLOW}⚠${NC} WARNING: Using example merchant seed!"
    echo "  For production, generate a new seed:"
    echo "    cd tools && python generate_merchant_wallet.py"
    echo ""
fi

# Stop existing containers
echo ""
echo -e "${BLUE}[3/5]${NC} Cleaning up old containers..."
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓${NC} Cleanup complete"

# Build and start services
echo ""
echo -e "${BLUE}[4/5]${NC} Building and starting services..."
echo "  This may take a few minutes on first run..."

docker-compose up -d --build

# Wait for services to be healthy
echo ""
echo -e "${BLUE}[5/5]${NC} Waiting for services to start..."

MAX_WAIT=60
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Check API health
    if curl -s http://localhost/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} All services are running!"
        break
    fi

    echo -n "."
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    echo -e "${RED}✗${NC} Services failed to start within ${MAX_WAIT}s"
    echo "  Check logs: docker-compose logs"
    exit 1
fi

# Get merchant address
HEALTH=$(curl -s http://localhost/health)
MERCHANT_ADDR=$(echo "$HEALTH" | grep -o '"merchant_address":"[^"]*"' | cut -d'"' -f4)

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       Startup Complete! 🚀            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo "Services running:"
echo ""
echo -e "  ${BLUE}Web Dashboard:${NC}    http://localhost"
echo -e "  ${BLUE}API Endpoint:${NC}     http://localhost/api"
echo -e "  ${BLUE}API Health:${NC}       http://localhost/health"
echo ""
echo "Merchant Information:"
echo ""
echo -e "  ${BLUE}Address:${NC}          ${MERCHANT_ADDR}"
echo ""
echo "Next Steps:"
echo ""
echo "  1. Open Dashboard:    ${BLUE}http://localhost${NC}"
echo ""
echo "  2. Run Demo Setup:"
echo "     ${BLUE}bash scripts/demo-setup.sh${NC}"
echo ""
echo "  3. Register a Device:"
echo "     ${BLUE}curl -X POST http://localhost:3000/devices/register \\${NC}"
echo "       ${BLUE}-H \"Content-Type: application/json\" \\${NC}"
echo "       ${BLUE}-d '{\"device_id\":\"test-001\",\"exposure_cap_drops\":3000000}'${NC}"
echo ""
echo "  4. View Logs:"
echo "     ${BLUE}docker-compose logs -f${NC}"
echo ""
echo "  5. Stop Services:"
echo "     ${BLUE}docker-compose down${NC}"
echo ""
echo "Documentation:"
echo ""
echo "  • Architecture:  ${BLUE}docs/ARCHITECTURE.md${NC}"
echo "  • Deployment:    ${BLUE}docs/DEPLOYMENT.md${NC}"
echo "  • ESP32 Setup:   ${BLUE}firmware/esp32_vending/README.md${NC}"
echo ""
echo "Support:"
echo ""
echo "  • Issues:        ${BLUE}https://github.com/your-org/xrpl-offline-payments/issues${NC}"
echo "  • Email:         ${BLUE}support@xacceptapay.com${NC}"
echo ""
echo -e "${GREEN}Happy building! 🎉${NC}"
