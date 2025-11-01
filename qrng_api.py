#!/usr/bin/env python3
"""
QRNG API Server with x402 Payment Integration

Provides quantum random number generation as a service with pay-per-request
using the x402 protocol for frictionless crypto payments.

Features:
- True quantum randomness from IBM Quantum computers
- Pay-per-API-call using x402 protocol (USDC on Base/Solana/etc)
- Multiple output formats (hex, base64, bytes, integers)
- Configurable pricing per endpoint
- No accounts or registration required
"""

import os
import json
import secrets
import base64
import hashlib
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps

import httpx
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import the quantum wallet generator from the project
from main import EnhancedQuantumWalletGenerator

# Load environment variables
load_dotenv()

# Configuration
FACILITATOR_URL = os.getenv("X402_FACILITATOR_URL", "https://facilitator.x402.rs")
PAYMENT_RECEIVER_ADDRESS = os.getenv("X402_RECEIVER_ADDRESS", "0xYourAddress")
DEFAULT_NETWORK = os.getenv("X402_DEFAULT_NETWORK", "base")  # base, solana, polygon, etc
IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_CHANNEL = os.getenv("IBM_QUANTUM_CHANNEL", "ibm_quantum")

# Pricing configuration (in USD)
PRICING = {
    "/qrng/bytes": {"price": 0.01, "description": "Generate quantum random bytes"},
    "/qrng/hex": {"price": 0.01, "description": "Generate quantum random hex string"},
    "/qrng/integers": {"price": 0.02, "description": "Generate quantum random integers"},
    "/qrng/uuid": {"price": 0.01, "description": "Generate quantum-based UUID"},
    "/qrng/entropy": {"price": 0.05, "description": "Generate high-entropy quantum seed"},
}

# Initialize FastAPI app
app = FastAPI(
    title="QRNG API",
    description="Quantum Random Number Generation API powered by IBM Quantum and x402 payments",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Models ====================

class QRNGBytesRequest(BaseModel):
    """Request model for generating quantum random bytes"""
    length: int = Field(default=32, ge=1, le=1024, description="Number of random bytes to generate")
    format: str = Field(default="hex", pattern="^(hex|base64|base64url)$", description="Output format")


class QRNGIntegersRequest(BaseModel):
    """Request model for generating quantum random integers"""
    count: int = Field(default=10, ge=1, le=100, description="Number of random integers to generate")
    min_value: int = Field(default=0, description="Minimum value (inclusive)")
    max_value: int = Field(default=100, description="Maximum value (exclusive)")


class QRNGEntropyRequest(BaseModel):
    """Request model for generating high-entropy quantum seed"""
    bits: int = Field(default=256, ge=128, le=512, description="Number of entropy bits")


class PaymentInfo(BaseModel):
    """Payment information for x402 protocol"""
    signature: str
    nonce: str
    timestamp: int
    chain: str


# ==================== x402 Payment Middleware ====================

class X402PaymentVerifier:
    """Verifies x402 payment headers and processes payments via facilitator"""

    def __init__(self, facilitator_url: str, receiver_address: str):
        self.facilitator_url = facilitator_url
        self.receiver_address = receiver_address
        self.client = httpx.AsyncClient(timeout=30.0)
        self.used_nonces = {}  # In production, use Redis or database
        self._cleanup_interval = timedelta(hours=1)

    async def verify_payment(
        self,
        request: Request,
        required_price: float,
        network: str = DEFAULT_NETWORK,
    ) -> Dict[str, Any]:
        """
        Verify x402 payment headers against the facilitator

        Expected headers:
        - X-Payment-Signature: Signature from user's wallet
        - X-Payment-Nonce: Unique nonce to prevent replay attacks
        - X-Payment-Timestamp: Unix timestamp
        - X-Payment-Chain: Blockchain network (base, solana, etc)
        """

        # Extract payment headers
        signature = request.headers.get("X-Payment-Signature")
        nonce = request.headers.get("X-Payment-Nonce")
        timestamp = request.headers.get("X-Payment-Timestamp")
        chain = request.headers.get("X-Payment-Chain", network)

        if not all([signature, nonce, timestamp]):
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Payment required",
                    "message": "Missing x402 payment headers",
                    "required_headers": ["X-Payment-Signature", "X-Payment-Nonce", "X-Payment-Timestamp"],
                    "price": f"${required_price}",
                    "receiver": self.receiver_address,
                    "network": network,
                }
            )

        # Check timestamp (must be within 5 minutes)
        try:
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > 300:  # 5 minutes
                raise HTTPException(
                    status_code=402,
                    detail={"error": "Payment expired", "message": "Timestamp too old or in future"}
                )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid timestamp", "message": "Timestamp must be a Unix timestamp"}
            )

        # Check nonce (prevent replay attacks)
        if nonce in self.used_nonces:
            raise HTTPException(
                status_code=402,
                detail={"error": "Payment already used", "message": "Nonce has been used before"}
            )

        # Verify payment with facilitator
        try:
            verification_response = await self.client.post(
                f"{self.facilitator_url}/verify",
                json={
                    "signature": signature,
                    "nonce": nonce,
                    "timestamp": request_time,
                    "chain": chain,
                    "receiver": self.receiver_address,
                    "amount": required_price,
                    "path": str(request.url.path),
                }
            )

            if verification_response.status_code == 200:
                # Mark nonce as used
                self.used_nonces[nonce] = current_time
                self._cleanup_old_nonces()

                return verification_response.json()
            elif verification_response.status_code == 402:
                error_data = verification_response.json()
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Payment verification failed",
                        "message": error_data.get("message", "Invalid payment"),
                        "facilitator_response": error_data,
                    }
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Facilitator error",
                        "message": "Could not verify payment with facilitator"
                    }
                )

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Network error",
                    "message": f"Could not connect to payment facilitator: {str(e)}"
                }
            )

    def _cleanup_old_nonces(self):
        """Remove old nonces to prevent memory bloat"""
        current_time = int(time.time())
        cutoff_time = current_time - 3600  # Keep nonces for 1 hour

        self.used_nonces = {
            nonce: timestamp
            for nonce, timestamp in self.used_nonces.items()
            if timestamp > cutoff_time
        }


# Initialize payment verifier
payment_verifier = X402PaymentVerifier(FACILITATOR_URL, PAYMENT_RECEIVER_ADDRESS)


def require_payment(endpoint_path: str):
    """Decorator to require payment for an endpoint"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            pricing_info = PRICING.get(endpoint_path)
            if not pricing_info:
                raise HTTPException(status_code=500, detail="Endpoint pricing not configured")

            # Verify payment
            await payment_verifier.verify_payment(
                request=request,
                required_price=pricing_info["price"],
            )

            # Payment verified, proceed with request
            return await func(*args, request=request, **kwargs)

        return wrapper
    return decorator


# ==================== Quantum RNG Service ====================

class QuantumRNGService:
    """Service for generating quantum random numbers using IBM Quantum"""

    def __init__(self):
        self.wallet_generator = None
        self._initialize_quantum_service()

    def _initialize_quantum_service(self):
        """Initialize connection to IBM Quantum"""
        if not IBM_QUANTUM_TOKEN:
            raise ValueError("IBM_QUANTUM_TOKEN environment variable not set")

        try:
            self.wallet_generator = EnhancedQuantumWalletGenerator(
                ibm_token=IBM_QUANTUM_TOKEN,
                channel=IBM_QUANTUM_CHANNEL,
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize IBM Quantum service: {str(e)}")

    async def generate_quantum_bytes(self, length: int = 32) -> bytes:
        """
        Generate quantum random bytes

        Uses IBM Quantum computers for true quantum randomness,
        mixed with OS entropy for enhanced security.
        """
        # Generate quantum entropy (256 bits = 32 bytes)
        quantum_entropy = self.wallet_generator.generate_quantum_entropy(bits=256)

        # Generate OS entropy for mixing
        os_entropy = secrets.token_bytes(32)

        # Mix quantum and OS entropy using SHA-256
        mixed_entropy = hashlib.sha256(quantum_entropy + os_entropy).digest()

        # If more bytes needed, use HKDF-like expansion
        if length <= 32:
            return mixed_entropy[:length]
        else:
            result = mixed_entropy
            counter = 1
            while len(result) < length:
                next_block = hashlib.sha256(mixed_entropy + counter.to_bytes(4, 'big')).digest()
                result += next_block
                counter += 1
            return result[:length]

    async def generate_quantum_integers(
        self,
        count: int,
        min_value: int,
        max_value: int
    ) -> List[int]:
        """Generate quantum random integers in specified range"""
        range_size = max_value - min_value
        if range_size <= 0:
            raise ValueError("max_value must be greater than min_value")

        # Calculate bytes needed for random integers
        bytes_per_int = (range_size.bit_length() + 7) // 8
        total_bytes_needed = bytes_per_int * count * 2  # Extra for rejection sampling

        random_bytes = await self.generate_quantum_bytes(total_bytes_needed)

        integers = []
        byte_index = 0

        while len(integers) < count and byte_index + bytes_per_int <= len(random_bytes):
            # Convert bytes to integer
            random_int = int.from_bytes(
                random_bytes[byte_index:byte_index + bytes_per_int],
                byteorder='big'
            )
            byte_index += bytes_per_int

            # Rejection sampling to avoid modulo bias
            if random_int < (256 ** bytes_per_int // range_size) * range_size:
                integers.append(min_value + (random_int % range_size))

        return integers[:count]


# Initialize quantum RNG service
qrng_service = QuantumRNGService()


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """API information and pricing"""
    return {
        "name": "QRNG API",
        "description": "Quantum Random Number Generation powered by IBM Quantum",
        "version": "1.0.0",
        "payment": {
            "protocol": "x402",
            "facilitator": FACILITATOR_URL,
            "receiver": PAYMENT_RECEIVER_ADDRESS,
            "network": DEFAULT_NETWORK,
        },
        "endpoints": PRICING,
        "documentation": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint (no payment required)"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "quantum_service": "connected" if qrng_service.wallet_generator else "disconnected",
    }


@app.post("/qrng/bytes")
@require_payment("/qrng/bytes")
async def generate_bytes(request: Request, params: QRNGBytesRequest):
    """
    Generate quantum random bytes

    Payment required: $0.01 per request
    """
    try:
        random_bytes = await qrng_service.generate_quantum_bytes(params.length)

        # Format output
        if params.format == "hex":
            output = random_bytes.hex()
        elif params.format == "base64":
            output = base64.b64encode(random_bytes).decode('ascii')
        elif params.format == "base64url":
            output = base64.urlsafe_b64encode(random_bytes).decode('ascii')
        else:
            output = random_bytes.hex()  # Default to hex

        return {
            "success": True,
            "data": {
                "random": output,
                "format": params.format,
                "length": params.length,
            },
            "metadata": {
                "source": "ibm_quantum",
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate random bytes: {str(e)}")


@app.post("/qrng/hex")
@require_payment("/qrng/hex")
async def generate_hex(request: Request, length: int = 32):
    """
    Generate quantum random hex string

    Payment required: $0.01 per request
    """
    try:
        random_bytes = await qrng_service.generate_quantum_bytes(length)

        return {
            "success": True,
            "data": {
                "random": random_bytes.hex(),
                "length": length,
            },
            "metadata": {
                "source": "ibm_quantum",
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate random hex: {str(e)}")


@app.post("/qrng/integers")
@require_payment("/qrng/integers")
async def generate_integers(request: Request, params: QRNGIntegersRequest):
    """
    Generate quantum random integers

    Payment required: $0.02 per request
    """
    try:
        integers = await qrng_service.generate_quantum_integers(
            count=params.count,
            min_value=params.min_value,
            max_value=params.max_value,
        )

        return {
            "success": True,
            "data": {
                "random": integers,
                "count": len(integers),
                "range": {"min": params.min_value, "max": params.max_value},
            },
            "metadata": {
                "source": "ibm_quantum",
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate random integers: {str(e)}")


@app.post("/qrng/uuid")
@require_payment("/qrng/uuid")
async def generate_uuid(request: Request):
    """
    Generate quantum-based UUID v4

    Payment required: $0.01 per request
    """
    try:
        random_bytes = await qrng_service.generate_quantum_bytes(16)

        # Set UUID v4 version and variant bits
        random_bytes = bytearray(random_bytes)
        random_bytes[6] = (random_bytes[6] & 0x0F) | 0x40  # Version 4
        random_bytes[8] = (random_bytes[8] & 0x3F) | 0x80  # Variant 10

        # Format as UUID
        uuid_hex = bytes(random_bytes).hex()
        uuid_str = f"{uuid_hex[:8]}-{uuid_hex[8:12]}-{uuid_hex[12:16]}-{uuid_hex[16:20]}-{uuid_hex[20:]}"

        return {
            "success": True,
            "data": {
                "uuid": uuid_str,
            },
            "metadata": {
                "source": "ibm_quantum",
                "version": "uuid_v4",
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate UUID: {str(e)}")


@app.post("/qrng/entropy")
@require_payment("/qrng/entropy")
async def generate_entropy(request: Request, params: QRNGEntropyRequest):
    """
    Generate high-entropy quantum seed (for cryptographic use)

    Payment required: $0.05 per request

    This endpoint provides maximum security by using pure quantum entropy
    mixed with OS randomness, suitable for generating cryptographic keys,
    seeds, or other security-critical random data.
    """
    try:
        byte_length = (params.bits + 7) // 8
        random_bytes = await qrng_service.generate_quantum_bytes(byte_length)

        return {
            "success": True,
            "data": {
                "entropy": {
                    "hex": random_bytes.hex(),
                    "base64": base64.b64encode(random_bytes).decode('ascii'),
                },
                "bits": params.bits,
                "bytes": byte_length,
            },
            "metadata": {
                "source": "ibm_quantum",
                "security_level": "high",
                "entropy_sources": ["quantum", "os_random"],
                "timestamp": datetime.utcnow().isoformat(),
            },
            "warning": "Store this entropy securely. It should only be used once."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate entropy: {str(e)}")


# ==================== Error Handlers ====================

@app.exception_handler(402)
async def payment_required_handler(request: Request, exc: HTTPException):
    """Custom handler for 402 Payment Required errors"""
    return JSONResponse(
        status_code=402,
        content=exc.detail,
        headers={
            "X-Payment-Required": "true",
            "X-Payment-Protocol": "x402",
        }
    )


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn

    print("🌌 Starting QRNG API Server...")
    print(f"📡 x402 Facilitator: {FACILITATOR_URL}")
    print(f"💰 Payment Receiver: {PAYMENT_RECEIVER_ADDRESS}")
    print(f"🔗 Network: {DEFAULT_NETWORK}")
    print(f"🔬 Quantum Backend: IBM Quantum")
    print("\n📋 Pricing:")
    for endpoint, info in PRICING.items():
        print(f"  {endpoint}: ${info['price']} - {info['description']}")

    uvicorn.run(
        "qrng_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
