# QRNG API Documentation

> Quantum Random Number Generation API powered by IBM Quantum and x402 payments

## Overview

The QRNG API provides **true quantum random number generation** as a service using IBM Quantum computers. It integrates with the **x402 protocol** for frictionless, pay-per-request crypto payments.

### Why Quantum Random Numbers?

Traditional pseudo-random number generators (PRNGs) are deterministic and potentially predictable. **Quantum Random Number Generators (QRNGs)** leverage the inherent randomness of quantum mechanics to produce truly unpredictable random numbers.

**Use Cases:**
- 🎲 **Gaming & Gambling** - Provably fair random outcomes
- 🔐 **Cryptography** - Secure key generation
- 🤖 **AI & ML** - Unbiased random seeds and sampling
- 🔬 **Scientific Simulations** - Monte Carlo methods
- 🎨 **Creative Applications** - Generative art and music
- 🔑 **Identity Generation** - Unique identifiers and tokens

## Features

✨ **True Quantum Randomness** - Generated using real IBM Quantum computers, not simulators

💰 **Pay-Per-Use** - No subscriptions, accounts, or registration via x402 protocol

🌐 **Multi-Chain Support** - Base, Solana, Polygon, Avalanche, Sei, XDC

⚡ **Fast & Reliable** - High-quality entropy with low latency

🔒 **Secure** - Multi-layer entropy mixing (Quantum + OS randomness)

📊 **Multiple Formats** - Hex, Base64, integers, UUIDs, raw entropy

## Quick Start

### 1. Installation

Install dependencies:

```bash
# Using uv (recommended)
uv pip install -r pyproject.toml

# Or using pip
pip install fastapi uvicorn httpx pydantic qiskit qiskit-ibm-runtime eth-account
```

### 2. Configuration

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
# IBM Quantum Configuration
IBM_QUANTUM_TOKEN=your_ibm_quantum_token_here
IBM_QUANTUM_CHANNEL=ibm_quantum

# x402 Payment Configuration
X402_FACILITATOR_URL=https://facilitator.x402.rs
X402_RECEIVER_ADDRESS=0xYourWalletAddressHere
X402_DEFAULT_NETWORK=base
```

**Get IBM Quantum Token:**
1. Sign up at [https://quantum.ibm.com/](https://quantum.ibm.com/)
2. Go to Account Settings → API Token
3. Copy your token to `.env`

**Setup Payment Receiver:**
- Use your Ethereum wallet address (Base, Polygon, etc.)
- Or Solana wallet address for Solana network
- This is where you'll receive USDC payments

### 3. Start the Server

```bash
# Quick start with auto-setup
./run_qrng_api.sh

# Or manually
python qrng_api.py
```

The server will start at `http://localhost:8000`

### 4. Access the Interface

**Web Frontend (For Humans):**
- Open http://localhost:8000 in your browser
- Beautiful UI with gasless/signless x402 payments
- Click, pay, and get quantum random numbers instantly

**API Documentation (For Developers):**
- Interactive Swagger UI: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc
- API Info: http://localhost:8000/ (JSON response)

**JavaScript API (For AI Agents):**
```javascript
// In browser console or scripts
await QRNG_API.generateBytes(32, 'hex')
await QRNG_API.generateIntegers(10, 0, 100)
await QRNG_API.generateUUID()
await QRNG_API.generateEntropy(256)
```

## API Endpoints

### Free Endpoints (No Payment Required)

#### `GET /`
Get API information and pricing.

**Response:**
```json
{
  "name": "QRNG API",
  "version": "1.0.0",
  "payment": {
    "protocol": "x402",
    "facilitator": "https://facilitator.x402.rs",
    "receiver": "0xYourAddress",
    "network": "base"
  },
  "endpoints": {
    "/qrng/bytes": {
      "price": 0.01,
      "description": "Generate quantum random bytes"
    }
  }
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-01T12:00:00",
  "quantum_service": "connected"
}
```

---

### Paid Endpoints (x402 Payment Required)

All paid endpoints require x402 payment headers:

**Required Headers:**
```
X-Payment-Signature: <signature>
X-Payment-Nonce: <unique_nonce>
X-Payment-Timestamp: <unix_timestamp>
X-Payment-Chain: <network>
```

---

#### `POST /qrng/bytes`

Generate quantum random bytes.

**Price:** $0.01 per request

**Request Body:**
```json
{
  "length": 32,
  "format": "hex"
}
```

**Parameters:**
- `length` (int, 1-1024): Number of bytes to generate
- `format` (string): Output format - `hex`, `base64`, or `base64url`

**Response:**
```json
{
  "success": true,
  "data": {
    "random": "a3f5b2c8d1e4f6a7b9c0d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3",
    "format": "hex",
    "length": 32
  },
  "metadata": {
    "source": "ibm_quantum",
    "timestamp": "2025-11-01T12:00:00"
  }
}
```

---

#### `POST /qrng/hex`

Generate quantum random hex string.

**Price:** $0.01 per request

**Query Parameters:**
- `length` (int, default=32): Number of bytes

**Response:**
```json
{
  "success": true,
  "data": {
    "random": "a3f5b2c8d1e4f6a7b9c0d2e3f4a5b6c7",
    "length": 32
  },
  "metadata": {
    "source": "ibm_quantum",
    "timestamp": "2025-11-01T12:00:00"
  }
}
```

---

#### `POST /qrng/integers`

Generate quantum random integers.

**Price:** $0.02 per request

**Request Body:**
```json
{
  "count": 10,
  "min_value": 0,
  "max_value": 100
}
```

**Parameters:**
- `count` (int, 1-100): Number of integers to generate
- `min_value` (int): Minimum value (inclusive)
- `max_value` (int): Maximum value (exclusive)

**Response:**
```json
{
  "success": true,
  "data": {
    "random": [42, 17, 93, 8, 56, 71, 24, 88, 35, 62],
    "count": 10,
    "range": {"min": 0, "max": 100}
  },
  "metadata": {
    "source": "ibm_quantum",
    "timestamp": "2025-11-01T12:00:00"
  }
}
```

---

#### `POST /qrng/uuid`

Generate quantum-based UUID v4.

**Price:** $0.01 per request

**Response:**
```json
{
  "success": true,
  "data": {
    "uuid": "a3f5b2c8-d1e4-4f6a-9b9c-0d2e3f4a5b6c"
  },
  "metadata": {
    "source": "ibm_quantum",
    "version": "uuid_v4",
    "timestamp": "2025-11-01T12:00:00"
  }
}
```

---

#### `POST /qrng/entropy`

Generate high-entropy quantum seed (for cryptographic use).

**Price:** $0.05 per request

**Request Body:**
```json
{
  "bits": 256
}
```

**Parameters:**
- `bits` (int, 128-512): Number of entropy bits

**Response:**
```json
{
  "success": true,
  "data": {
    "entropy": {
      "hex": "a3f5b2c8d1e4f6a7b9c0d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3",
      "base64": "o/Wyyx1O9qe5wNLj9KW2x9jp8KGyPNTl9qe4ydDh8qM="
    },
    "bits": 256,
    "bytes": 32
  },
  "metadata": {
    "source": "ibm_quantum",
    "security_level": "high",
    "entropy_sources": ["quantum", "os_random"],
    "timestamp": "2025-11-01T12:00:00"
  },
  "warning": "Store this entropy securely. It should only be used once."
}
```

---

## Payment Integration

### x402 Protocol Overview

The **x402 protocol** enables **pay-per-request** payments using crypto (USDC) with:
- ✅ No accounts or registration
- ✅ Instant payments with zero fees
- ✅ Global and permissionless
- ✅ Sub-cent precision

### How Payments Work

1. **User Signs Payment** - Creates a cryptographic signature using wallet
2. **Payment Headers Sent** - Includes signature, nonce, timestamp
3. **Facilitator Verifies** - x402 facilitator validates payment on-chain
4. **API Grants Access** - Request processed if payment valid

### Payment Headers

Every paid API request requires these headers:

```
X-Payment-Signature: 0xabc123...  # Wallet signature
X-Payment-Nonce: unique_nonce_123 # Prevents replay attacks
X-Payment-Timestamp: 1698768000   # Unix timestamp
X-Payment-Chain: base              # Blockchain network
```

### Supported Networks

| Network | Chain ID | Token |
|---------|----------|-------|
| **Base Mainnet** | base | USDC |
| **Solana Mainnet** | solana | USDC |
| **Polygon PoS** | polygon | USDC |
| **Avalanche C-Chain** | avalanche | USDC |
| **Sei Mainnet** | sei | USDC |
| **XDC Mainnet** | xdc | USDC |

**Testnets:**
- Base Sepolia (`base-sepolia`)
- Solana Devnet (`solana-devnet`)
- Polygon Amoy (`polygon-amoy`)
- Avalanche Fuji (`avalanche-fuji`)

## Client Examples

### Python Client

See `qrng_api_client_example.py` for a full Python client implementation.

**Quick Example:**

```python
from qrng_api_client_example import QRNGClient

# Initialize client
client = QRNGClient(
    api_url="http://localhost:8000",
    private_key="0xYourPrivateKey",
    network="base"
)

# Generate random bytes
result = client.generate_bytes(length=32, format="hex")
print(result['data']['random'])

# Generate random integers
result = client.generate_integers(count=10, min_value=0, max_value=100)
print(result['data']['random'])

# Generate UUID
result = client.generate_uuid()
print(result['data']['uuid'])

client.close()
```

### cURL Example

```bash
# Get API info (no payment)
curl http://localhost:8000/

# Generate random bytes (with payment)
curl -X POST http://localhost:8000/qrng/bytes \
  -H "Content-Type: application/json" \
  -H "X-Payment-Signature: 0xabc123..." \
  -H "X-Payment-Nonce: unique_nonce_123" \
  -H "X-Payment-Timestamp: 1698768000" \
  -H "X-Payment-Chain: base" \
  -d '{"length": 32, "format": "hex"}'
```

### JavaScript/TypeScript Example

```typescript
import axios from 'axios';
import { ethers } from 'ethers';

const API_URL = 'http://localhost:8000';
const wallet = new ethers.Wallet(privateKey);

async function generateQRNG() {
  // Create payment signature
  const timestamp = Math.floor(Date.now() / 1000);
  const nonce = ethers.utils.hexlify(ethers.utils.randomBytes(32));

  const message = JSON.stringify({
    endpoint: '/qrng/bytes',
    price: 0.01,
    receiver: receiverAddress,
    nonce: nonce,
    timestamp: timestamp,
    chain: 'base'
  });

  const signature = await wallet.signMessage(message);

  // Make API request
  const response = await axios.post(`${API_URL}/qrng/bytes`, {
    length: 32,
    format: 'hex'
  }, {
    headers: {
      'X-Payment-Signature': signature,
      'X-Payment-Nonce': nonce,
      'X-Payment-Timestamp': timestamp.toString(),
      'X-Payment-Chain': 'base'
    }
  });

  console.log(response.data.data.random);
}
```

## AI Agent Integration

QRNG API is designed for AI agents that need high-quality randomness:

### Use Cases for AI

1. **ML Model Initialization**
   ```python
   # Get quantum random seed for model
   seed = int(client.generate_entropy(bits=256)['data']['entropy']['hex'], 16)
   torch.manual_seed(seed)
   ```

2. **Random Sampling**
   ```python
   # Get random indices for data selection
   indices = client.generate_integers(count=100, min_value=0, max_value=10000)
   sampled_data = dataset[indices['data']['random']]
   ```

3. **Session IDs**
   ```python
   # Generate unique session identifier
   session_id = client.generate_uuid()['data']['uuid']
   ```

4. **Cryptographic Keys**
   ```python
   # Generate secure communication key
   key = bytes.fromhex(client.generate_bytes(32, 'hex')['data']['random'])
   ```

### AI Agent Client

See `AIAgentQRNGClient` class in `qrng_api_client_example.py`:

```python
from qrng_api_client_example import AIAgentQRNGClient

agent_client = AIAgentQRNGClient(
    api_url="http://localhost:8000",
    private_key="0xYourPrivateKey"
)

# Get random seed for ML
seed = agent_client.get_random_seed_for_ml(bits=256)

# Get random samples
indices = agent_client.get_random_samples(count=100, min_val=0, max_val=1000)

# Get session ID
session_id = agent_client.get_session_id()

# Get crypto key
key = agent_client.get_crypto_key(key_size=32)
```

## Error Handling

### 402 Payment Required

When payment is missing or invalid:

```json
{
  "error": "Payment required",
  "message": "Missing x402 payment headers",
  "required_headers": [
    "X-Payment-Signature",
    "X-Payment-Nonce",
    "X-Payment-Timestamp"
  ],
  "price": "$0.01",
  "receiver": "0xYourAddress",
  "network": "base"
}
```

### Common Errors

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Invalid Request | Bad parameters or malformed request |
| 402 | Payment Required | Missing or invalid payment |
| 500 | Server Error | Internal server or quantum service error |

## Security

### Entropy Sources

The QRNG API uses **multi-layer entropy mixing**:

1. **Quantum Entropy** (256 bits) - From IBM Quantum computers
2. **OS Entropy** (256 bits) - From system CSPRNG
3. **Mixing** - SHA-256 based mixing for enhanced security

**Why mix?** Even if IBM Quantum could observe the quantum measurements, they cannot derive the final output due to the one-way mixing with OS entropy.

### Payment Security

- **Nonce Protection** - Prevents replay attacks
- **Timestamp Validation** - Rejects old/future payments (5-minute window)
- **Signature Verification** - Cryptographic proof via x402 facilitator
- **No Account Needed** - Wallet-based authentication only

### Best Practices

✅ **Do:**
- Use high-entropy endpoints for cryptographic keys
- Store generated entropy securely
- Use unique nonces for each request
- Keep private keys secure
- Validate API responses

❌ **Don't:**
- Reuse nonces (will be rejected)
- Share your private key
- Use low-quality endpoints for security-critical operations
- Cache entropy for later use (generate fresh each time)

## Deployment

### Production Deployment

1. **Update Configuration**
   ```env
   X402_RECEIVER_ADDRESS=0xYourProductionWallet
   X402_DEFAULT_NETWORK=base
   IBM_QUANTUM_TOKEN=your_production_token
   ```

2. **Use HTTPS**
   ```bash
   # Behind reverse proxy (nginx/caddy)
   # Or use uvicorn with SSL
   uvicorn qrng_api:app --host 0.0.0.0 --port 443 \
     --ssl-keyfile=/path/to/key.pem \
     --ssl-certfile=/path/to/cert.pem
   ```

3. **Use Redis for Nonces**
   Replace in-memory nonce storage with Redis for production:
   ```python
   import redis
   self.redis = redis.Redis(host='localhost', port=6379)
   ```

4. **Monitor Quantum Service**
   Set up health check monitoring and alerting

5. **Rate Limiting**
   Add rate limiting middleware to prevent abuse

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "qrng_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t qrng-api .
docker run -p 8000:8000 --env-file .env qrng-api
```

## Troubleshooting

### IBM Quantum Connection Issues

**Problem:** "Failed to initialize IBM Quantum service"

**Solutions:**
- Check IBM_QUANTUM_TOKEN is valid
- Verify network connectivity
- Check IBM Quantum service status at https://quantum.ibm.com/

### Payment Verification Fails

**Problem:** "Payment verification failed"

**Solutions:**
- Ensure timestamp is current (within 5 minutes)
- Use unique nonce for each request
- Verify signature is correctly generated
- Check receiver address matches configuration
- Confirm sufficient funds in wallet

### Slow API Responses

**Problem:** API requests taking too long

**Reasons:**
- Quantum job queue on IBM Quantum
- Using real quantum hardware (not simulator)
- Network latency to IBM Quantum cloud

**Solutions:**
- This is expected for real quantum hardware
- Consider caching for batch operations
- Use faster endpoints for non-critical randomness

## Pricing

| Endpoint | Price | Description |
|----------|-------|-------------|
| `/qrng/bytes` | $0.01 | Random bytes (1-1024 bytes) |
| `/qrng/hex` | $0.01 | Random hex string |
| `/qrng/integers` | $0.02 | Random integers (1-100) |
| `/qrng/uuid` | $0.01 | UUID v4 generation |
| `/qrng/entropy` | $0.05 | High-entropy seed (128-512 bits) |

**Payment:** USDC on supported networks via x402 protocol

## Support & Resources

- **GitHub**: [Your Repository URL]
- **x402 Protocol**: https://x402.rs/
- **x402 Facilitator**: https://facilitator.x402.rs
- **IBM Quantum**: https://quantum.ibm.com/
- **API Documentation**: http://your-api-url/docs

## License

[Your License Here]

## Acknowledgments

- **IBM Quantum** - For providing access to real quantum computers
- **x402 Protocol** - For frictionless payment infrastructure
- **FastAPI** - For the excellent web framework

---

**Built with ❤️ using true quantum randomness**
