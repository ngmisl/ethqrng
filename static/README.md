# QRNG API Frontend

Simple HTML/CSS/JavaScript frontend for the Quantum Random Number Generation API.

## Features

- **Clean, Modern UI** - Dark theme with gradient accents
- **x402 Payment Integration** - Gasless/signless payments via x402 protocol
- **Real-time Status** - Shows API and quantum service health
- **Multiple QRNG Endpoints** - Bytes, integers, UUIDs, and high-entropy seeds
- **AI-Friendly** - Programmatic JavaScript API for AI agents
- **Responsive Design** - Works on desktop and mobile

## How It Works

### For Humans

1. **Visit the Frontend** - Open http://localhost:8000 in your browser
2. **Choose Generation Type** - Select from random bytes, integers, UUID, or entropy
3. **Configure Parameters** - Set length, range, format, etc.
4. **Pay & Generate** - Click button → x402 payment modal → quantum randomness delivered
5. **Copy Results** - Click copy button to use the generated random data

### For AI Agents

The frontend exposes a JavaScript API at `window.QRNG_API`:

```javascript
// Generate random bytes
const result = await QRNG_API.generateBytes(32, 'hex');
console.log(result.data.random);

// Generate random integers
const ints = await QRNG_API.generateIntegers(10, 0, 100);
console.log(ints.data.random);

// Generate UUID
const uuid = await QRNG_API.generateUUID();
console.log(uuid.data.uuid);

// Generate high-entropy seed
const entropy = await QRNG_API.generateEntropy(256);
console.log(entropy.data.entropy.hex);
```

## x402 Payments

### Gasless & Signless

The x402 protocol enables **gasless and signless** payments:

- **No Wallet Connection** - No MetaMask popup or wallet signing
- **No Gas Fees** - x402 facilitator handles on-chain transactions
- **Instant Payment** - Pay and get results immediately
- **Sub-cent Pricing** - From $0.01 per request

### How Payments Work

1. **User Clicks Generate** - Payment modal shows price and details
2. **User Confirms Payment** - JavaScript calls x402 facilitator
3. **Facilitator Verifies** - x402 handles on-chain payment
4. **API Returns Data** - Quantum random numbers delivered
5. **No Blockchain Interaction Needed** - All handled by x402

### Payment Headers

The JavaScript automatically includes x402 payment headers:

```
X-Payment-Signature: <generated_signature>
X-Payment-Nonce: <unique_nonce>
X-Payment-Timestamp: <unix_timestamp>
X-Payment-Chain: base
```

## Files

- **index.html** - Main HTML structure and UI components
- **style.css** - Dark theme styling with gradients
- **app.js** - API client and x402 payment handling
- **README.md** - This file

## Development

### Local Testing

```bash
# Start the API server
./run_qrng_api.sh

# Or manually
python qrng_api.py

# Open in browser
open http://localhost:8000
```

### Customization

**Change Theme Colors** - Edit CSS variables in `style.css`:
```css
:root {
    --primary-color: #6366f1;
    --secondary-color: #8b5cf6;
    --bg-color: #0f172a;
    /* ... */
}
```

**Add New Endpoints** - Add to `app.js`:
```javascript
async function generateCustom() {
    await callAPIWithPayment(
        '/qrng/custom',
        'POST',
        { params },
        'customResult',
        (data) => formatCustomResult(data)
    );
}
```

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design

## Security

- **CORS Enabled** - API accepts requests from any origin
- **HTTPS Recommended** - Use HTTPS in production
- **Payment Verification** - x402 facilitator validates all payments
- **Nonce Protection** - Prevents replay attacks
- **Timestamp Validation** - 5-minute payment window

## API Endpoints Used

| Endpoint | Price | Description |
|----------|-------|-------------|
| `POST /qrng/bytes` | $0.01 | Generate quantum random bytes |
| `POST /qrng/integers` | $0.02 | Generate random integers |
| `POST /qrng/uuid` | $0.01 | Generate UUID v4 |
| `POST /qrng/entropy` | $0.05 | Generate high-entropy seed |
| `GET /health` | Free | Health check |

## Deployment

### Production Checklist

- [ ] Update x402 receiver address in `.env`
- [ ] Set production network (base, solana, etc.)
- [ ] Enable HTTPS
- [ ] Configure CDN for static files (optional)
- [ ] Set up monitoring for API uptime
- [ ] Test payment flow on mainnet

### CDN Deployment

You can deploy static files to a CDN and point to the API:

```javascript
// In app.js, update API_BASE
const API_BASE = 'https://api.yourdomain.com';
```

Then serve HTML/CSS/JS from:
- Cloudflare Pages
- Vercel
- Netlify
- AWS S3 + CloudFront

## License

[Your License Here]
