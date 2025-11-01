// QRNG API Client - JavaScript
// Handles quantum random number generation with x402 payments

const API_BASE = window.location.origin;
let apiInfo = null;
let currentPaymentContext = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await checkAPIStatus();
    await loadAPIInfo();
});

// Check API Health Status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        updateStatus(data.status === 'healthy', data.quantum_service);
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatus(false, 'disconnected');
    }
}

// Load API Information
async function loadAPIInfo() {
    try {
        const response = await fetch(`${API_BASE}/`);
        apiInfo = await response.json();

        // Update UI with API info
        document.getElementById('paymentNetwork').textContent = apiInfo.payment?.network || 'Unknown';
        document.getElementById('facilitator').textContent = apiInfo.payment?.facilitator || 'Unknown';
        document.getElementById('networkBadge').textContent = `${apiInfo.payment?.network || 'base'} Network`;

        console.log('API Info loaded:', apiInfo);
    } catch (error) {
        console.error('Failed to load API info:', error);
    }
}

// Update Status Display
function updateStatus(healthy, quantumStatus) {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const statusDot = statusIndicator.querySelector('.status-dot');
    const quantumStatusEl = document.getElementById('quantumStatus');

    if (healthy) {
        statusText.textContent = 'API Online';
        statusDot.style.background = '#10b981'; // green
    } else {
        statusText.textContent = 'API Offline';
        statusDot.style.background = '#ef4444'; // red
    }

    quantumStatusEl.textContent = quantumStatus === 'connected' ? '✓ Connected' : '✗ Disconnected';
}

// Show Loading
function showLoading(message = 'Processing quantum computation...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    loadingText.textContent = message;
    overlay.classList.add('show');
}

// Hide Loading
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('show');
}

// Show Payment Modal
function showPaymentModal(price, endpoint) {
    const modal = document.getElementById('paymentModal');
    const amountEl = document.getElementById('paymentAmount');
    const chainEl = document.getElementById('paymentChain');
    const receiverEl = document.getElementById('paymentReceiver');

    amountEl.textContent = `$${price.toFixed(2)}`;
    chainEl.textContent = apiInfo?.payment?.network || 'base';
    receiverEl.textContent = apiInfo?.payment?.receiver || '—';

    currentPaymentContext = { price, endpoint };
    modal.classList.add('show');
}

// Close Payment Modal
function closePaymentModal() {
    const modal = document.getElementById('paymentModal');
    modal.classList.remove('show');
    currentPaymentContext = null;
}

// Process Payment (x402 Gasless/Signless) - PRODUCTION
async function processPayment() {
    if (!currentPaymentContext) return;

    closePaymentModal();
    showLoading('Initiating payment via x402 facilitator...');

    try {
        // Step 1: Request payment from x402 facilitator
        const paymentRequest = await createX402Payment({
            amount: currentPaymentContext.price,
            receiver: apiInfo.payment.receiver,
            chain: apiInfo.payment.network,
            endpoint: currentPaymentContext.endpoint,
        });

        showLoading('Processing payment on-chain...');

        // Step 2: Wait for facilitator to process (gasless transaction)
        const paymentProof = await waitForPaymentConfirmation(paymentRequest.paymentId);

        showLoading('Verifying payment...');

        // Step 3: Store payment headers for API call
        currentPaymentContext.headers = {
            'X-Payment-Signature': paymentProof.signature,
            'X-Payment-Nonce': paymentProof.nonce,
            'X-Payment-Timestamp': paymentProof.timestamp.toString(),
            'X-Payment-Chain': apiInfo.payment.network,
            'X-Payment-Id': paymentProof.paymentId,
        };

        // Step 4: Proceed with the actual API call
        await currentPaymentContext.callback();

    } catch (error) {
        hideLoading();
        console.error('Payment error:', error);
        showError('Payment failed: ' + error.message);
    }
}

// Create x402 Payment via Facilitator - PRODUCTION
async function createX402Payment({ amount, receiver, chain, endpoint }) {
    const facilitatorUrl = apiInfo.payment.facilitator;

    try {
        const response = await fetch(`${facilitatorUrl}/create-payment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: amount,
                receiver: receiver,
                chain: chain,
                metadata: {
                    endpoint: endpoint,
                    service: 'qrng-api',
                }
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to create payment');
        }

        const data = await response.json();
        return {
            paymentId: data.paymentId,
            paymentUrl: data.paymentUrl, // URL for user to complete payment if needed
            status: data.status,
        };
    } catch (error) {
        console.error('x402 payment creation failed:', error);
        throw new Error(`Failed to create payment: ${error.message}`);
    }
}

// Wait for Payment Confirmation from x402 Facilitator - PRODUCTION
async function waitForPaymentConfirmation(paymentId, maxAttempts = 30) {
    const facilitatorUrl = apiInfo.payment.facilitator;
    let attempts = 0;

    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`${facilitatorUrl}/payment-status/${paymentId}`);

            if (!response.ok) {
                throw new Error('Failed to check payment status');
            }

            const status = await response.json();

            if (status.status === 'confirmed') {
                // Payment confirmed, return proof
                return {
                    paymentId: paymentId,
                    signature: status.signature,
                    nonce: status.nonce,
                    timestamp: status.timestamp,
                    txHash: status.txHash,
                };
            } else if (status.status === 'failed') {
                throw new Error('Payment failed: ' + (status.error || 'Unknown error'));
            }

            // Payment still pending, wait and retry
            await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
            attempts++;

        } catch (error) {
            console.error('Payment status check failed:', error);
            throw error;
        }
    }

    throw new Error('Payment timeout: Transaction not confirmed within expected time');
}

// Generate Random Nonce
function generateNonce() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// Make API Call with Payment
async function callAPIWithPayment(endpoint, method, body, resultElementId, formatResult) {
    const price = apiInfo?.endpoints?.[endpoint]?.price || 0.01;

    // Store callback for after payment
    currentPaymentContext = {
        price,
        endpoint,
        callback: async () => {
            try {
                const headers = {
                    'Content-Type': 'application/json',
                    ...currentPaymentContext.headers
                };

                const options = {
                    method: method,
                    headers: headers
                };

                if (body) {
                    options.body = JSON.stringify(body);
                }

                const response = await fetch(`${API_BASE}${endpoint}`, options);
                const data = await response.json();

                hideLoading();

                if (response.ok) {
                    showResult(resultElementId, formatResult(data), true);
                } else {
                    // Handle 402 Payment Required
                    if (response.status === 402) {
                        showError('Payment verification failed. Please try again.');
                    } else {
                        showError(data.detail || 'Request failed');
                    }
                }
            } catch (error) {
                hideLoading();
                showError('API call failed: ' + error.message);
            }
        }
    };

    // Show payment modal
    showPaymentModal(price, endpoint);
}

// Generate Random Bytes
async function generateBytes() {
    const length = parseInt(document.getElementById('bytesLength').value);
    const format = document.getElementById('bytesFormat').value;

    await callAPIWithPayment(
        '/qrng/bytes',
        'POST',
        { length, format },
        'bytesResult',
        (data) => formatBytesResult(data, format)
    );
}

// Generate Random Integers
async function generateIntegers() {
    const count = parseInt(document.getElementById('intCount').value);
    const min_value = parseInt(document.getElementById('intMin').value);
    const max_value = parseInt(document.getElementById('intMax').value);

    if (min_value >= max_value) {
        showError('Max value must be greater than min value');
        return;
    }

    await callAPIWithPayment(
        '/qrng/integers',
        'POST',
        { count, min_value, max_value },
        'integersResult',
        (data) => formatIntegersResult(data)
    );
}

// Generate UUID
async function generateUUID() {
    await callAPIWithPayment(
        '/qrng/uuid',
        'POST',
        null,
        'uuidResult',
        (data) => formatUUIDResult(data)
    );
}

// Generate Entropy
async function generateEntropy() {
    const bits = parseInt(document.getElementById('entropyBits').value);

    await callAPIWithPayment(
        '/qrng/entropy',
        'POST',
        { bits },
        'entropyResult',
        (data) => formatEntropyResult(data)
    );
}

// Format Results
function formatBytesResult(data, format) {
    return `
        <div class="result-label">Quantum Random ${format.toUpperCase()}</div>
        <div class="result-value">${data.data.random}</div>
        <div class="result-label">Length: ${data.data.length} bytes</div>
        <div class="result-label">Source: ${data.metadata.source}</div>
        <button class="copy-btn" onclick="copyToClipboard('${data.data.random}')">Copy</button>
    `;
}

function formatIntegersResult(data) {
    return `
        <div class="result-label">Quantum Random Integers</div>
        <div class="result-value">${JSON.stringify(data.data.random)}</div>
        <div class="result-label">Count: ${data.data.count} | Range: ${data.data.range.min}-${data.data.range.max}</div>
        <div class="result-label">Source: ${data.metadata.source}</div>
        <button class="copy-btn" onclick="copyToClipboard('${JSON.stringify(data.data.random)}')">Copy</button>
    `;
}

function formatUUIDResult(data) {
    return `
        <div class="result-label">Quantum UUID v4</div>
        <div class="result-value">${data.data.uuid}</div>
        <div class="result-label">Version: ${data.metadata.version}</div>
        <div class="result-label">Source: ${data.metadata.source}</div>
        <button class="copy-btn" onclick="copyToClipboard('${data.data.uuid}')">Copy</button>
    `;
}

function formatEntropyResult(data) {
    const hex = data.data.entropy.hex;
    const displayHex = hex.length > 64 ? hex.substring(0, 64) + '...' : hex;

    return `
        <div class="result-label">High-Entropy Quantum Seed</div>
        <div class="result-value">${displayHex}</div>
        <div class="result-label">Bits: ${data.data.bits} | Bytes: ${data.data.bytes}</div>
        <div class="result-label">Security: ${data.metadata.security_level} | Sources: ${data.metadata.entropy_sources.join(', ')}</div>
        <div class="result-label" style="color: var(--warning-color);">${data.warning}</div>
        <button class="copy-btn" onclick="copyToClipboard('${hex}')">Copy Full Hex</button>
        <button class="copy-btn" onclick="copyToClipboard('${data.data.entropy.base64}')">Copy Base64</button>
    `;
}

// Show Result
function showResult(elementId, content, success = true) {
    const element = document.getElementById(elementId);
    element.innerHTML = content;
    element.className = success ? 'result show success' : 'result show error';
}

// Show Error
function showError(message) {
    alert('Error: ' + message);
}

// Copy to Clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);

        // Show temporary success message
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        btn.style.background = '#10b981';

        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    } catch (error) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);

        alert('Copied to clipboard!');
    }
}

// API for AI Agents - Programmatic Access
window.QRNG_API = {
    // Generate random bytes programmatically
    async generateBytes(length = 32, format = 'hex') {
        return await this._call('/qrng/bytes', { length, format });
    },

    // Generate random integers programmatically
    async generateIntegers(count = 10, min_value = 0, max_value = 100) {
        return await this._call('/qrng/integers', { count, min_value, max_value });
    },

    // Generate UUID programmatically
    async generateUUID() {
        return await this._call('/qrng/uuid', {});
    },

    // Generate entropy programmatically
    async generateEntropy(bits = 256) {
        return await this._call('/qrng/entropy', { bits });
    },

    // Internal API call method - PRODUCTION
    async _call(endpoint, body) {
        const price = apiInfo?.endpoints?.[endpoint]?.price || 0.01;

        // Step 1: Create payment with x402 facilitator
        const paymentRequest = await createX402Payment({
            amount: price,
            receiver: apiInfo.payment.receiver,
            chain: apiInfo.payment.network,
            endpoint: endpoint,
        });

        // Step 2: Wait for payment confirmation
        const paymentProof = await waitForPaymentConfirmation(paymentRequest.paymentId);

        // Step 3: Call API with payment proof
        const headers = {
            'Content-Type': 'application/json',
            'X-Payment-Signature': paymentProof.signature,
            'X-Payment-Nonce': paymentProof.nonce,
            'X-Payment-Timestamp': paymentProof.timestamp.toString(),
            'X-Payment-Chain': apiInfo.payment.network,
            'X-Payment-Id': paymentProof.paymentId,
        };

        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail?.message || `API call failed: ${response.status}`);
        }

        return await response.json();
    }
};

// Log API availability for AI agents
console.log('QRNG API available at window.QRNG_API');
console.log('Example usage:');
console.log('  await QRNG_API.generateBytes(32, "hex")');
console.log('  await QRNG_API.generateIntegers(10, 0, 100)');
console.log('  await QRNG_API.generateUUID()');
console.log('  await QRNG_API.generateEntropy(256)');
