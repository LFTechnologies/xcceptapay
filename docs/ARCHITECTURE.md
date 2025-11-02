# Architecture Documentation

## System Overview

XRPL Offline Payments enables merchants to accept XRPL PayChannel payments without internet connectivity, with eventual settlement to the XRP Ledger.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     XRPL Testnet/Mainnet                      │
│              (PayChannel Settlement Layer)                    │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ Settlement
                         │ (when online)
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                      Backend API Server                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Express.js  │  │   MongoDB    │  │    Redis     │        │
│  │  REST API    │◄─┤  (Claims DB) │  │  (Cache/RL)  │        │
│  └──────┬───────┘  └──────────────┘  └──────────────┘        │
│         │                                                       │
│         │ Claim Verification (Offline)                         │
│         │ Settlement Queue Management                          │
│         │ Device Registration                                  │
└─────────┼──────────────────────────────────────────────────────┘
          │
          │ HTTP/WebSocket
          │
┌─────────┼──────────────────────────────────────────────────────┐
│         ▼                                                       │
│  ┌────────────┐         ┌────────────┐                        │
│  │  Web UI    │         │  Mobile    │                        │
│  │ Dashboard  │         │  Wallet    │                        │
│  │ (React)    │         │  (Kivy)    │                        │
│  └────────────┘         └──────┬─────┘                        │
│                                 │                              │
│                                 │ BLE                          │
│                                 │                              │
│                         ┌───────▼──────┐                       │
│                         │  ESP32 + BLE │                       │
│                         │  + Relay     │                       │
│                         │  (Vending)   │                       │
│                         └──────────────┘                       │
└──────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Frontend Layer

#### Web Dashboard (React + TypeScript)
- **Technology**: React 18, TypeScript, Vite, Tailwind CSS
- **Purpose**: Merchant management interface
- **Features**:
  - Real-time claim monitoring
  - Device registration
  - Settlement controls
  - Analytics dashboards
  - Transaction history

**Key Components**:
```
frontend/
├── src/
│   ├── components/
│   │   └── Layout.tsx         # Main layout with navigation
│   ├── pages/
│   │   ├── Dashboard.tsx      # Overview & stats
│   │   ├── Devices.tsx        # Device management
│   │   ├── Claims.tsx         # Claim processing
│   │   ├── Receipts.tsx       # Settlement history
│   │   └── Settings.tsx       # Configuration
│   ├── lib/
│   │   ├── api.ts             # API client
│   │   └── utils.ts           # Helper functions
│   └── types/
│       └── index.ts           # TypeScript definitions
```

#### Mobile Wallet (Kivy + Python)
- **Technology**: Kivy, Python 3.10+, xrpl-py
- **Purpose**: Offline claim verification and BLE communication
- **Features**:
  - Wallet seed/key management
  - Offline PayChannel claim verification (Ed25519 signatures)
  - BLE communication with ESP32 devices
  - Local exposure cap enforcement
  - Optional API synchronization

**Architecture**:
```python
# Offline Verification Flow
1. Receive claim JSON (BLE or manual input)
2. Verify signature locally using xrpl-py
3. Check exposure cap (local storage)
4. Send vend command via BLE (if verified)
5. Queue claim to API (when online)
```

### 2. Backend Layer

#### API Server (Node.js + Express)
- **Technology**: Node.js 20, Express 5, xrpl.js
- **Purpose**: Claim queue management, settlement orchestration

**Core Modules**:

```javascript
// api/server_offline_dev.js

1. Claim Verification (/claims/verify)
   - Uses ripple-binary-codec for message encoding
   - ripple-keypairs for Ed25519 verification
   - Validates: channel_id, amount, signature, pubkey

2. Claim Queue (/claims/queue)
   - Stores verified claims
   - Enforces monotonic increase
   - Checks exposure caps per device

3. Settlement (/claims/settle)
   - Submits PaymentChannelClaim to XRPL
   - Updates ledger balances
   - Creates receipts for audit

4. Device Management (/devices/register)
   - Assigns destination tags
   - Configures per-device exposure caps
```

**Database Schema** (MongoDB):
```javascript
// Devices Collection
{
  device_id: String,
  dest_tag: Number (unique),
  exposure_cap_drops: Number,
  created_at: Date
}

// Channels Collection
{
  channel_id: String (64 hex),
  dest_address: String,
  dest_tag: Number,
  last_settled_drops: Number,
  last_seen_drops: Number
}

// Claims Collection (Queue)
{
  channel_id: String,
  amount_drops: Number,
  signature: String,
  pubkey: String,
  seenAt: Date
}

// Receipts Collection
{
  channel_id: String,
  tx_hash: String,
  amount_drops: Number,
  ledger_index: Number,
  settledAt: Date
}
```

### 3. Device Layer

#### ESP32 Firmware
- **Technology**: Arduino, BLE libraries, U8g2 (OLED)
- **Purpose**: Offline vend approval, relay control

**State Machine**:
```
STATE_IDLE
   │
   ├─ BLE Connect ──► STATE_BLE_CONNECTED
   │                         │
   │                         ├─ Receive Claim ──► STATE_CLAIM_RECEIVED
   │                         │                           │
   │                         │                           ├─ Verify ──► STATE_CLAIM_VERIFIED
   │                         │                                              │
   │                         │                                              ├─ Vend ──► STATE_VENDING
   │                         │                                                             │
   │                         │                                                             ├─► STATE_TRANSACTION_COMPLETE
   │                         │                                                                         │
   │                         ◄───────────────────────────────────────────────────────────────────────┘
   │
   └─ Error ──► STATE_ERROR ──► (Display error) ──► STATE_IDLE
```

**BLE Protocol**:
```
Service UUID:     12345678-1234-5678-1234-56789abcdef0

Characteristics:
  TX (Notify/Read):  ESP32 → Kivy (status messages)
  RX (Write):        Kivy → ESP32 (commands)

Commands:
  1. Vend (JSON):
     {
       "action": "vend",
       "slot": 1,
       "pulse_ms": 600,
       "claim_channel": "...",
       "claim_amount_drops": "...",
       "device_id": "..."
     }

  2. Status (JSON):
     { "action": "status" }
```

## Data Flow

### Offline Payment Flow

```
1. Buyer Opens PayChannel
   ┌─────────────┐
   │   Buyer     │ Creates PayChannel on XRPL
   │   Wallet    │ (e.g., 10 XRP channel to merchant)
   └─────┬───────┘
         │
         ▼
   [Channel Created on Ledger]
   Channel ID: A1B2C3...
   Amount: 10,000,000 drops
   Destination: merchant address + dest_tag

2. Buyer Goes Offline
   ┌─────────────┐
   │   Buyer     │ Generates signed claim (offline)
   │   Wallet    │ channel_id, amount, signature, pubkey
   └─────┬───────┘
         │
         ▼
   Claim JSON (QR code or NFC transfer)

3. Merchant Receives Claim (Offline)
   ┌─────────────┐
   │   Kivy      │ Scans QR / BLE transfer
   │    App      │ Verifies signature locally
   └─────┬───────┘
         │ Signature valid?
         │
         ├─ YES ──► Check exposure cap
         │              │
         │              ├─ Within limit ──► Trigger BLE vend
         │              │                        │
         │              │                        ▼
         │              │                   ┌──────────┐
         │              │                   │  ESP32   │
         │              │                   │  Relay   │
         │              │                   │  Vends   │
         │              │                   └──────────┘
         │              │                        │
         │              │                        ▼
         │              │                   Update local state
         │              │                   (last_seen_drops)
         │              │
         │              └─ Over limit ──► Reject (402 Payment Required)
         │
         └─ NO ──► Reject (400 Bad Request)

4. Settlement (When Online)
   ┌─────────────┐
   │   Kivy      │ Uploads claim to API
   │    App      │ /claims/queue
   └─────┬───────┘
         │
         ▼
   ┌─────────────┐
   │     API     │ Re-verifies claim
   │   Server    │ Queues for settlement
   └─────┬───────┘
         │
         │ Manual or automatic trigger
         │
         ▼
   ┌─────────────┐
   │     API     │ Submits PaymentChannelClaim tx
   │   Server    │ to XRPL Testnet/Mainnet
   └─────┬───────┘
         │
         ▼
   [XRPL Ledger]
   Updates channel balance
   Merchant receives XRP
   Creates receipt
```

### Security Model

#### Cryptographic Verification

**PayChannel Claim Structure**:
```
Message = {
  channel: 64-char hex channel ID
  amount: cumulative drops (string)
}

Signed Message = encodeForSigningClaim(channel, amount)
              = "CLM\0" + channel_bytes + amount_bytes

Signature = Ed25519.sign(signed_message, buyer_private_key)
```

**Offline Verification**:
```python
# Kivy app (offline)
from xrpl.core.binarycodec import encode_for_signing_claim
from xrpl.core.keypairs import verify

msg = encode_for_signing_claim(channel=channel_id, amount=amount_drops)
valid = verify(message=msg, signature=sig, public_key=pubkey)

# If valid and within exposure cap:
#   → Allow vend
# Else:
#   → Reject
```

#### Double-Spend Prevention

1. **Monotonic Amounts**: Each claim must have amount > last_seen_drops
2. **Exposure Cap**: `(current_claim - last_settled) ≤ exposure_cap`
3. **Settlement Priority**: Highest claim per channel settled first

#### Threat Model

**Protected Against**:
- ✅ Invalid signatures (cryptographic verification)
- ✅ Replay attacks (monotonic amounts)
- ✅ Double-spend (exposure caps)
- ✅ Unauthorized devices (BLE pairing, device registration)

**Limitations**:
- ⚠️ Buyer can reuse old signed claims (merchant MUST track last_seen)
- ⚠️ Offline window limited by exposure cap
- ⚠️ Merchant assumes risk of unsettled claims

## Scalability

### Horizontal Scaling

```
┌────────────┐
│   Nginx    │  Load Balancer
└──────┬─────┘
       │
   ┌───┴───┬───────┬───────┐
   │       │       │       │
┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐
│ API │ │ API │ │ API │ │ API │  Stateless API instances
│  1  │ │  2  │ │  3  │ │  N  │
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
   │       │       │       │
   └───┬───┴───────┴───┬───┘
       │               │
   ┌───▼─────┐    ┌────▼────┐
   │ MongoDB │    │  Redis  │
   │ Cluster │    │ Cluster │
   └─────────┘    └─────────┘
```

### Performance Metrics

**Target Performance**:
- Claim verification: < 50ms (offline)
- API response time: < 200ms (p95)
- Settlement time: < 10s (XRPL confirmation)
- Throughput: 100 claims/sec per API instance

**Bottlenecks**:
1. XRPL RPC latency (mitigated with connection pooling)
2. MongoDB write throughput (mitigated with indexes)
3. BLE connection reliability (mitigated with retries)

## Deployment Topology

### Development
```
Single Host (localhost):
- API: http://localhost:3000
- Frontend: http://localhost:3001
- MongoDB: localhost:27017
- Redis: localhost:6379
```

### Staging (Docker Compose)
```
Single Server:
- Nginx (reverse proxy)
- API (3 replicas)
- Frontend (static hosting)
- MongoDB (single instance)
- Redis (single instance)
```

### Production (Kubernetes)
```
Multi-Node Cluster:
- Ingress Controller (SSL termination)
- API (5+ pods, auto-scaling)
- Frontend (CDN + static hosting)
- MongoDB Atlas (managed, replica set)
- Redis Cloud (managed, cluster)
- Monitoring (Prometheus, Grafana)
```

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Frontend | React | 18.2+ | Web UI |
| State Mgmt | React Query | 5.x | Server state |
| Styling | Tailwind CSS | 3.x | UI styling |
| Mobile | Kivy | 2.x | Offline wallet |
| Backend | Node.js | 20+ | API server |
| Framework | Express | 5.x | HTTP routing |
| Database | MongoDB | 7.0 | Persistent storage |
| Cache | Redis | 7.x | Rate limiting |
| XRPL Lib | xrpl.js | 4.x | Ledger interaction |
| Firmware | Arduino | 2.x | ESP32 programming |
| BLE | ESP32 BLE | - | Wireless comms |
| Display | U8g2 | 2.x | OLED graphics |

## Monitoring & Observability

### Metrics

```javascript
// API Metrics (Prometheus format)
- api_requests_total{method, path, status}
- api_request_duration_seconds{method, path}
- claim_verifications_total{result}
- settlements_total{result, simulated}
- settlement_amount_drops{channel_id}
- active_channels_gauge
- exposure_used_drops{device_id}
```

### Logging

```javascript
// Structured Logging (JSON)
{
  "level": "info",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "component": "claim-verifier",
  "channel_id": "A1B2C3...",
  "amount_drops": 2000000,
  "result": "valid",
  "duration_ms": 45
}
```

### Tracing

- Request ID propagation
- Distributed tracing (Jaeger/Zipkin)
- Claim lifecycle tracking

## Security Architecture

### Authentication & Authorization

```
User ──► Web Dashboard ──► JWT Token ──► API
                                         │
                                         ├─ Verify JWT
                                         ├─ Check role (user/admin/merchant)
                                         └─ Allow/Deny
```

### API Security Layers

1. **Network**: Firewall, VPC
2. **Transport**: HTTPS/TLS 1.3
3. **Application**: JWT, rate limiting
4. **Data**: Encryption at rest (MongoDB)

## Disaster Recovery

### Backup Strategy

- **MongoDB**: Daily automated backups (30-day retention)
- **Merchant Seed**: Offline encrypted storage
- **Configuration**: Version controlled (Git)

### Recovery Procedures

1. **API Failure**: Auto-restart (Docker/K8s)
2. **Database Corruption**: Restore from backup
3. **Lost Merchant Seed**: Recover from offline backup
4. **XRPL Network Issue**: Queue claims, retry on recovery

## Future Enhancements

### Phase 2
- Multi-signature wallets
- Webhooks for real-time notifications
- Mobile SDK for iOS/Android
- WebSocket for live updates

### Phase 3
- Lightning Network integration
- Cross-currency support
- Advanced analytics (ML fraud detection)
- Hardware wallet integration

## References

- [XRP Ledger Payment Channels](https://xrpl.org/payment-channels.html)
- [BLE GATT Specification](https://www.bluetooth.com/specifications/gatt/)
- [Ed25519 Signature Scheme](https://ed25519.cr.yp.to/)

## License

MIT
