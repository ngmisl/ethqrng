# x402 Production Deployment Guide

This guide explains how to deploy the QRNG API with production x402 payment integration.

## Overview

The system uses the **x402 protocol** for gasless, signless crypto payments. The architecture involves:

1. **Frontend** (HTML/CSS/JS) - User interface and payment initiation
2. **x402 Facilitator** - Handles on-chain transactions (gasless/signless)
3. **QRNG API Backend** - Verifies payments and generates quantum random numbers
4. **IBM Quantum** - Provides true quantum randomness

## x402 Payment Flow

### For Humans (Web Interface)

```
User clicks "Generate"
    ↓
Payment Modal shows price
    ↓
User clicks "Pay & Continue"
    ↓
Frontend calls x402 Facilitator API
POST /create-payment {amount, receiver, chain}
    ↓
Facilitator creates gasless transaction
(User pays USDC, no gas fees)
    ↓
Frontend polls for confirmation
GET /payment-status/{paymentId}
    ↓
Facilitator returns payment proof
{signature, nonce, timestamp, txHash}
    ↓
Frontend calls QRNG API with proof headers
POST /qrng/bytes
Headers: X-Payment-Signature, X-Payment-Nonce, etc.
    ↓
Backend verifies with Facilitator
POST /verify-payment {signature, nonce, ...}
    ↓
Facilitator confirms payment is valid
    ↓
Backend generates quantum random numbers
    ↓
Result returned to user
```

### For AI Agents (Programmatic)

```javascript
// AI agent calls exposed API
const result = await window.QRNG_API.generateBytes(32, 'hex');

// Internally, same flow as above
// Payment is handled automatically
```

## Production Setup

### 1. x402 Facilitator Configuration

You need access to an x402 facilitator. Options:

**Option A: Use Public Facilitator**
```env
X402_FACILITATOR_URL=https://facilitator.x402.rs
```

**Option B: Run Your Own Facilitator**
```bash
# Clone x402 facilitator
git clone https://github.com/x402/facilitator
cd facilitator

# Configure
cp .env.example .env
# Set your relayer wallet private key
# Set supported chains

# Deploy
docker-compose up -d
```

### 2. Environment Configuration

Update `.env` with production values:

```env
# IBM Quantum (Production)
IBM_QUANTUM_TOKEN=your_production_ibm_token
IBM_QUANTUM_CHANNEL=ibm_quantum

# x402 Payment (Production)
X402_FACILITATOR_URL=https://facilitator.x402.rs
X402_RECEIVER_ADDRESS=0xYourProductionWallet  # Where USDC is received
X402_DEFAULT_NETWORK=base  # base, solana, polygon, etc

# API Server
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Receiver Wallet Setup

The receiver address must:
- Be a valid wallet on the chosen network (Base, Solana, etc.)
- Be controlled by you (you receive the payments)
- Have minimal USDC to verify (optional)

**For Base:**
```
0xYourEthereumAddress
```

**For Solana:**
```
YourSolanaPublicKey
```

### 4. Facilitator API Endpoints

The backend expects these endpoints on the facilitator:

#### `POST /create-payment`

Create a new payment request.

**Request:**
```json
{
  "amount": 0.01,
  "receiver": "0xReceiverAddress",
  "chain": "base",
  "metadata": {
    "endpoint": "/qrng/bytes",
    "service": "qrng-api"
  }
}
```

**Response:**
```json
{
  "paymentId": "pay_abc123",
  "paymentUrl": "https://facilitator.x402.rs/pay/pay_abc123",
  "status": "pending"
}
```

#### `GET /payment-status/{paymentId}`

Check payment status.

**Response (Pending):**
```json
{
  "paymentId": "pay_abc123",
  "status": "pending"
}
```

**Response (Confirmed):**
```json
{
  "paymentId": "pay_abc123",
  "status": "confirmed",
  "signature": "0xabc123...",
  "nonce": "nonce_abc123",
  "timestamp": 1698768000,
  "txHash": "0xtxhash...",
  "amount": 0.01,
  "chain": "base"
}
```

#### `POST /verify-payment`

Verify a payment proof (called by backend).

**Request:**
```json
{
  "signature": "0xabc123...",
  "nonce": "nonce_abc123",
  "timestamp": 1698768000,
  "chain": "base",
  "receiver": "0xReceiverAddress",
  "amount": 0.01,
  "endpoint": "/qrng/bytes",
  "payment_id": "pay_abc123"
}
```

**Response:**
```json
{
  "valid": true,
  "amount": 0.01,
  "receiver": "0xReceiverAddress",
  "chain": "base",
  "txHash": "0xtxhash..."
}
```

### 5. Frontend Configuration

No changes needed! The frontend automatically:
- Detects facilitator URL from API info
- Creates payments via facilitator
- Polls for confirmation
- Sends proof to backend

### 6. Backend Verification

The backend (`qrng_api.py`) automatically:
- Extracts payment headers
- Calls facilitator `/verify-payment`
- Validates amount matches
- Checks nonce isn't reused
- Returns data if valid

## Testing

### Test with Testnet

Use testnet for initial testing:

```env
X402_DEFAULT_NETWORK=base-sepolia
X402_RECEIVER_ADDRESS=0xYourTestWallet
```

Get testnet USDC:
- Base Sepolia: [Sepolia Faucet](https://sepoliafaucet.com/)
- Polygon Amoy: [Amoy Faucet](https://faucet.polygon.technology/)

### Test Payment Flow

1. Visit http://localhost:8000
2. Click "Generate Random Bytes"
3. Click "Pay & Continue"
4. Watch browser console for payment flow
5. Verify payment on block explorer
6. Check results are returned

### Debug Mode

Enable debug logging:

```javascript
// In static/app.js
const DEBUG = true;

// Logs all payment steps
console.log('Payment request:', paymentRequest);
console.log('Payment proof:', paymentProof);
```

## Production Checklist

- [ ] x402 facilitator running and accessible
- [ ] Production receiver wallet configured
- [ ] Testnet payments working
- [ ] Mainnet USDC funded for testing
- [ ] IBM Quantum production token set
- [ ] HTTPS enabled (SSL certificate)
- [ ] Rate limiting configured
- [ ] Monitoring and alerts set up
- [ ] Error tracking (Sentry, etc.)
- [ ] Backup facilitator URL (optional)

## Security Considerations

### Nonce Storage

**Development (In-Memory):**
```python
self.used_nonces = {}  # Lost on restart
```

**Production (Redis):**
```python
import redis
self.redis = redis.Redis(host='localhost', port=6379)

# Store nonce
self.redis.setex(f"nonce:{nonce}", 3600, "1")

# Check nonce
if self.redis.exists(f"nonce:{nonce}"):
    raise HTTPException(...)
```

### Timestamp Validation

Current: 10-minute window (600 seconds)

Adjust based on needs:
```python
if abs(current_time - request_time) > 600:  # 10 minutes
```

### Amount Verification

Ensures exact amount paid:
```python
if abs(verification_data.get("amount", 0) - required_price) > 0.0001:
    raise HTTPException(...)
```

## Monitoring

### Key Metrics

1. **Payment Success Rate**
   - Track successful vs failed payments
   - Alert if below threshold

2. **Payment Confirmation Time**
   - How long from request to confirmation
   - Alert if taking too long

3. **Facilitator Uptime**
   - Monitor facilitator availability
   - Failover if down

4. **API Response Time**
   - Track quantum generation time
   - Alert if slow

### Logging

Add structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Log payment attempts
logger.info("Payment verification started", extra={
    "payment_id": payment_id,
    "amount": required_price,
    "endpoint": request.url.path
})

# Log payment success
logger.info("Payment verified successfully", extra={
    "payment_id": payment_id,
    "tx_hash": verification_data.get("txHash")
})
```

## Troubleshooting

### "Failed to create payment"

**Cause:** Facilitator not accessible or rejecting request

**Fix:**
1. Check facilitator URL is correct
2. Verify receiver address format
3. Check facilitator logs
4. Ensure chain is supported

### "Payment timeout"

**Cause:** Payment not confirmed within 30 seconds

**Fix:**
1. Check blockchain network status
2. Increase timeout (`maxAttempts` in frontend)
3. Verify USDC balance in user wallet
4. Check facilitator transaction logs

### "Payment already used"

**Cause:** Nonce reused (replay attack prevention)

**Fix:**
- This is expected behavior
- User should retry with new request
- Check for frontend bugs causing double-submission

### "Payment amount mismatch"

**Cause:** Amount paid doesn't match required price

**Fix:**
1. Ensure frontend sends correct amount
2. Check for rounding errors
3. Verify facilitator returns accurate amount

## Scaling

### Horizontal Scaling

Run multiple API instances behind load balancer:

```nginx
upstream qrng_api {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    location / {
        proxy_pass http://qrng_api;
    }
}
```

**Important:** Use Redis for nonce storage when scaling!

### Caching

Cache API info response:

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_api_info():
    return {
        "name": "QRNG API",
        # ...
    }
```

### Database

For production, store payments in database:

```python
# models.py
from sqlalchemy import Column, String, Float, DateTime

class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String, primary_key=True)
    amount = Column(Float)
    receiver = Column(String)
    tx_hash = Column(String)
    status = Column(String)
    created_at = Column(DateTime)
```

## Support

For issues:
- x402 Protocol: https://x402.rs/docs
- QRNG API: See QRNG_API.md
- IBM Quantum: https://quantum.ibm.com/support

## License

[Your License Here]
