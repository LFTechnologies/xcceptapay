#!/bin/bash

# XRPL Offline Payments - Demo Setup Script
# This script initializes the system with demo data for testing and presentations

set -e

echo "================================"
echo "XRPL Offline Payments Demo Setup"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="${API_URL:-http://localhost:3000}"
MERCHANT_SEED="${MERCHANT_SEED:-}"

echo -e "${BLUE}[1/6]${NC} Checking API health..."
HEALTH=$(curl -s "${API_URL}/health" || echo "{\"ok\":false}")
if echo "$HEALTH" | grep -q '"ok":true'; then
    echo -e "${GREEN}✓${NC} API is healthy"
    MERCHANT_ADDR=$(echo "$HEALTH" | grep -o '"merchant_address":"[^"]*"' | cut -d'"' -f4)
    echo -e "  Merchant Address: ${MERCHANT_ADDR}"
else
    echo -e "${YELLOW}⚠${NC} API not responding at ${API_URL}"
    echo "  Make sure the API is running: cd api && npm start"
    exit 1
fi

echo ""
echo -e "${BLUE}[2/6]${NC} Registering demo devices..."

# Register vending machine
echo "  → Registering vending-001 (Food Truck)"
RESPONSE=$(curl -s -X POST "${API_URL}/devices/register" \
    -H "Content-Type: application/json" \
    -d '{
        "device_id": "vending-001",
        "exposure_cap_drops": 3000000
    }')

DEST_TAG_1=$(echo "$RESPONSE" | grep -o '"dest_tag":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✓${NC} Registered with dest_tag: ${DEST_TAG_1}"

# Register POS terminal
echo "  → Registering pos-terminal-001 (Coffee Shop)"
RESPONSE=$(curl -s -X POST "${API_URL}/devices/register" \
    -H "Content-Type: application/json" \
    -d '{
        "device_id": "pos-terminal-001",
        "exposure_cap_drops": 5000000
    }')

DEST_TAG_2=$(echo "$RESPONSE" | grep -o '"dest_tag":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✓${NC} Registered with dest_tag: ${DEST_TAG_2}"

# Register kiosk
echo "  → Registering kiosk-downtown-01 (City Kiosk)"
RESPONSE=$(curl -s -X POST "${API_URL}/devices/register" \
    -H "Content-Type: application/json" \
    -d '{
        "device_id": "kiosk-downtown-01",
        "exposure_cap_drops": 2000000
    }')

DEST_TAG_3=$(echo "$RESPONSE" | grep -o '"dest_tag":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✓${NC} Registered with dest_tag: ${DEST_TAG_3}"

echo ""
echo -e "${BLUE}[3/6]${NC} Creating demo PayChannel claims..."
echo "  NOTE: For demo purposes, we'll simulate claim creation"
echo "  In production, use tools/buyer_claim_tool.py to create real claims"

# Create MongoDB init script with demo data
cat > /tmp/demo-seed.js <<EOF
// MongoDB demo seed data
db = db.getSiblingDB('xcceptapay');

// Demo channels
db.channels.insertMany([
    {
        channel_id: "A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E9F0A1B2",
        dest_address: "${MERCHANT_ADDR}",
        dest_tag: ${DEST_TAG_1},
        last_settled_drops: 0,
        last_seen_drops: 0,
        created_at: new Date()
    },
    {
        channel_id: "B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E9F0A1B2C3",
        dest_address: "${MERCHANT_ADDR}",
        dest_tag: ${DEST_TAG_2},
        last_settled_drops: 0,
        last_seen_drops: 0,
        created_at: new Date()
    }
]);

// Demo receipts (simulated settlements)
db.receipts.insertMany([
    {
        channel_id: "A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E9F0A1B2",
        tx_hash: "DEMO_TX_" + Math.random().toString(36).substring(7).toUpperCase(),
        amount_drops: 1500000,
        ledger_index: 12345678,
        settledAt: new Date(Date.now() - 3600000),
        simulated: true
    },
    {
        channel_id: "B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E9F0A1B2C3",
        tx_hash: "DEMO_TX_" + Math.random().toString(36).substring(7).toUpperCase(),
        amount_drops: 2500000,
        ledger_index: 12345679,
        settledAt: new Date(Date.now() - 7200000),
        simulated: true
    },
    {
        channel_id: "A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E9F0A1B2",
        tx_hash: "DEMO_TX_" + Math.random().toString(36).substring(7).toUpperCase(),
        amount_drops: 750000,
        ledger_index: 12345680,
        settledAt: new Date(Date.now() - 1800000),
        simulated: true
    }
]);

print("✓ Demo data seeded successfully");
EOF

echo -e "${GREEN}✓${NC} Demo seed script created"

echo ""
echo -e "${BLUE}[4/6]${NC} Creating demo claim JSON files..."

mkdir -p demo-claims

# Demo claim 1 (2 XRP)
cat > demo-claims/claim-2xrp.json <<EOF
{
  "channel_id": "A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E9F0A1B2",
  "amount_drops": "2000000",
  "signature": "304502210098765432109876543210987654321098765432109876543210987654321098765432102201FEDCBA09876543210FEDCBA09876543210FEDCBA09876543210FEDCBA0987654321",
  "pubkey": "ED0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF",
  "device_id": "vending-001"
}
EOF

# Demo claim 2 (1.5 XRP)
cat > demo-claims/claim-1.5xrp.json <<EOF
{
  "channel_id": "B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E9F0A1B2C3",
  "amount_drops": "1500000",
  "signature": "30450221009ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF01234567890220ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789AB",
  "pubkey": "EDABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789",
  "device_id": "pos-terminal-001"
}
EOF

echo -e "${GREEN}✓${NC} Created demo claim files in ./demo-claims/"

echo ""
echo -e "${BLUE}[5/6]${NC} Generating QR codes for merchant..."
echo "  Merchant Address: ${MERCHANT_ADDR}"
echo "  Destination Tags: ${DEST_TAG_1}, ${DEST_TAG_2}, ${DEST_TAG_3}"

# Create quick reference file
cat > demo-merchant-info.txt <<EOF
=== XRPL Offline Payments - Demo Merchant Info ===

Merchant Address: ${MERCHANT_ADDR}

Registered Devices:
  1. vending-001 (Food Truck)
     - Destination Tag: ${DEST_TAG_1}
     - Exposure Cap: 3 XRP

  2. pos-terminal-001 (Coffee Shop)
     - Destination Tag: ${DEST_TAG_2}
     - Exposure Cap: 5 XRP

  3. kiosk-downtown-01 (City Kiosk)
     - Destination Tag: ${DEST_TAG_3}
     - Exposure Cap: 2 XRP

API Endpoints:
  - Health: ${API_URL}/health
  - Register Device: POST ${API_URL}/devices/register
  - Queue Claim: POST ${API_URL}/claims/queue
  - Settle: POST ${API_URL}/claims/settle
  - Receipts: GET ${API_URL}/receipts

Demo Claims:
  - ./demo-claims/claim-2xrp.json (2 XRP claim)
  - ./demo-claims/claim-1.5xrp.json (1.5 XRP claim)

Next Steps:
  1. Open web dashboard: http://localhost:3001
  2. Test Kivy app with demo claims
  3. Use buyer tools to create real PayChannels on Testnet
EOF

echo -e "${GREEN}✓${NC} Created demo-merchant-info.txt"

echo ""
echo -e "${BLUE}[6/6]${NC} Demo setup complete!"
echo ""
echo "================================================"
echo -e "${GREEN}✓ Demo Environment Ready${NC}"
echo "================================================"
echo ""
echo "What to do next:"
echo ""
echo "1. Open Web Dashboard:"
echo "   → http://localhost:3001"
echo ""
echo "2. View API health:"
echo "   → curl ${API_URL}/health | jq"
echo ""
echo "3. Test with Kivy app:"
echo "   → cd app && python main.py"
echo "   → Load claim from: demo-claims/claim-2xrp.json"
echo ""
echo "4. Create real PayChannel (Testnet):"
echo "   → cd tools"
echo "   → python buyer_claim_tool_compat.py open-and-claim \\"
echo "       --destination ${MERCHANT_ADDR} \\"
echo "       --dest-tag ${DEST_TAG_1} \\"
echo "       --amount-xrp 2 --cum-xrp 2 --use-faucet"
echo ""
echo "5. Monitor receipts:"
echo "   → curl ${API_URL}/receipts | jq"
echo ""
echo "Demo data files created:"
echo "  - demo-claims/claim-2xrp.json"
echo "  - demo-claims/claim-1.5xrp.json"
echo "  - demo-merchant-info.txt"
echo "  - /tmp/demo-seed.js (MongoDB seed)"
echo ""
echo "Happy testing! 🚀"
