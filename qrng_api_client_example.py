#!/usr/bin/env python3
"""
QRNG API Client Example

Demonstrates how to call the QRNG API with x402 payment integration.

This example shows:
1. How to generate payment signatures for x402 protocol
2. How to make API requests with payment headers
3. Different QRNG endpoints and their usage
4. Error handling for payment failures

Note: This is a simplified example. In production, you would use a proper
Web3 library to sign transactions and interact with your wallet.
"""

import os
import time
import secrets
import hashlib
import json
from typing import Dict, Any

import httpx
from eth_account import Account
from eth_account.messages import encode_defunct
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("QRNG_API_URL", "http://localhost:8000")
PRIVATE_KEY = os.getenv("USER_PRIVATE_KEY")  # Your wallet private key for signing
NETWORK = os.getenv("X402_NETWORK", "base")


class QRNGClient:
    """Client for interacting with QRNG API using x402 payments"""

    def __init__(self, api_url: str, private_key: str, network: str = "base"):
        """
        Initialize QRNG API client

        Args:
            api_url: Base URL of the QRNG API
            private_key: Your Ethereum private key (with 0x prefix)
            network: Blockchain network (base, solana, polygon, etc)
        """
        self.api_url = api_url.rstrip('/')
        self.network = network
        self.client = httpx.Client(timeout=30.0)

        # Initialize account for signing
        if private_key:
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            self.account = Account.from_key(private_key)
            self.address = self.account.address
        else:
            self.account = None
            self.address = None

    def _generate_payment_headers(
        self,
        endpoint: str,
        price: float,
        receiver: str
    ) -> Dict[str, str]:
        """
        Generate x402 payment headers

        In a production implementation, this would:
        1. Create a payment transaction on-chain
        2. Sign the transaction with your private key
        3. Submit to the x402 facilitator
        4. Return the payment proof headers

        This is a simplified example for demonstration.
        """
        if not self.account:
            raise ValueError("Private key not configured. Cannot generate payment signature.")

        # Generate unique nonce
        nonce = secrets.token_hex(32)

        # Current timestamp
        timestamp = int(time.time())

        # Create message to sign (this format depends on x402 spec)
        # Typically includes: endpoint, price, receiver, nonce, timestamp
        message_data = {
            "endpoint": endpoint,
            "price": price,
            "receiver": receiver,
            "nonce": nonce,
            "timestamp": timestamp,
            "chain": self.network,
        }
        message = json.dumps(message_data, sort_keys=True)

        # Sign the message
        message_hash = encode_defunct(text=message)
        signed_message = self.account.sign_message(message_hash)
        signature = signed_message.signature.hex()

        # Return x402 payment headers
        return {
            "X-Payment-Signature": signature,
            "X-Payment-Nonce": nonce,
            "X-Payment-Timestamp": str(timestamp),
            "X-Payment-Chain": self.network,
        }

    def get_info(self) -> Dict[str, Any]:
        """Get API information and pricing (no payment required)"""
        response = self.client.get(f"{self.api_url}/")
        response.raise_for_status()
        return response.json()

    def get_health(self) -> Dict[str, Any]:
        """Health check (no payment required)"""
        response = self.client.get(f"{self.api_url}/health")
        response.raise_for_status()
        return response.json()

    def generate_bytes(
        self,
        length: int = 32,
        format: str = "hex"
    ) -> Dict[str, Any]:
        """
        Generate quantum random bytes

        Args:
            length: Number of bytes to generate (1-1024)
            format: Output format (hex, base64, base64url)

        Returns:
            API response with random bytes
        """
        # Get API info to find receiver address and price
        info = self.get_info()
        receiver = info["payment"]["receiver"]
        price = info["endpoints"]["/qrng/bytes"]["price"]

        # Generate payment headers
        headers = self._generate_payment_headers("/qrng/bytes", price, receiver)

        # Make request
        response = self.client.post(
            f"{self.api_url}/qrng/bytes",
            json={"length": length, "format": format},
            headers=headers,
        )

        if response.status_code == 402:
            raise Exception(f"Payment required: {response.json()}")

        response.raise_for_status()
        return response.json()

    def generate_hex(self, length: int = 32) -> Dict[str, Any]:
        """Generate quantum random hex string"""
        info = self.get_info()
        receiver = info["payment"]["receiver"]
        price = info["endpoints"]["/qrng/hex"]["price"]

        headers = self._generate_payment_headers("/qrng/hex", price, receiver)

        response = self.client.post(
            f"{self.api_url}/qrng/hex",
            params={"length": length},
            headers=headers,
        )

        if response.status_code == 402:
            raise Exception(f"Payment required: {response.json()}")

        response.raise_for_status()
        return response.json()

    def generate_integers(
        self,
        count: int = 10,
        min_value: int = 0,
        max_value: int = 100
    ) -> Dict[str, Any]:
        """Generate quantum random integers"""
        info = self.get_info()
        receiver = info["payment"]["receiver"]
        price = info["endpoints"]["/qrng/integers"]["price"]

        headers = self._generate_payment_headers("/qrng/integers", price, receiver)

        response = self.client.post(
            f"{self.api_url}/qrng/integers",
            json={
                "count": count,
                "min_value": min_value,
                "max_value": max_value,
            },
            headers=headers,
        )

        if response.status_code == 402:
            raise Exception(f"Payment required: {response.json()}")

        response.raise_for_status()
        return response.json()

    def generate_uuid(self) -> Dict[str, Any]:
        """Generate quantum-based UUID"""
        info = self.get_info()
        receiver = info["payment"]["receiver"]
        price = info["endpoints"]["/qrng/uuid"]["price"]

        headers = self._generate_payment_headers("/qrng/uuid", price, receiver)

        response = self.client.post(
            f"{self.api_url}/qrng/uuid",
            headers=headers,
        )

        if response.status_code == 402:
            raise Exception(f"Payment required: {response.json()}")

        response.raise_for_status()
        return response.json()

    def generate_entropy(self, bits: int = 256) -> Dict[str, Any]:
        """Generate high-entropy quantum seed"""
        info = self.get_info()
        receiver = info["payment"]["receiver"]
        price = info["endpoints"]["/qrng/entropy"]["price"]

        headers = self._generate_payment_headers("/qrng/entropy", price, receiver)

        response = self.client.post(
            f"{self.api_url}/qrng/entropy",
            json={"bits": bits},
            headers=headers,
        )

        if response.status_code == 402:
            raise Exception(f"Payment required: {response.json()}")

        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP client"""
        self.client.close()


# ==================== Usage Examples ====================

def main():
    """Example usage of QRNG API client"""

    print("🌌 QRNG API Client Example\n")

    # Initialize client
    client = QRNGClient(
        api_url=API_BASE_URL,
        private_key=PRIVATE_KEY,
        network=NETWORK,
    )

    try:
        # 1. Get API information (no payment)
        print("📋 Getting API information...")
        info = client.get_info()
        print(f"   API: {info['name']} v{info['version']}")
        print(f"   Payment Network: {info['payment']['network']}")
        print(f"   Receiver: {info['payment']['receiver']}\n")

        # 2. Health check (no payment)
        print("🏥 Checking API health...")
        health = client.get_health()
        print(f"   Status: {health['status']}")
        print(f"   Quantum Service: {health['quantum_service']}\n")

        # 3. Generate random bytes
        print("🎲 Generating 32 random bytes (hex format)...")
        result = client.generate_bytes(length=32, format="hex")
        print(f"   Random: {result['data']['random']}")
        print(f"   Source: {result['metadata']['source']}\n")

        # 4. Generate random integers
        print("🎲 Generating 10 random integers (0-100)...")
        result = client.generate_integers(count=10, min_value=0, max_value=100)
        print(f"   Random: {result['data']['random']}")
        print(f"   Count: {result['data']['count']}\n")

        # 5. Generate UUID
        print("🆔 Generating quantum UUID...")
        result = client.generate_uuid()
        print(f"   UUID: {result['data']['uuid']}")
        print(f"   Version: {result['metadata']['version']}\n")

        # 6. Generate high-entropy seed
        print("🔐 Generating 256-bit entropy seed...")
        result = client.generate_entropy(bits=256)
        print(f"   Entropy (hex): {result['data']['entropy']['hex'][:64]}...")
        print(f"   Bits: {result['data']['bits']}")
        print(f"   Security Level: {result['metadata']['security_level']}\n")

        print("✅ All examples completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        client.close()


# ==================== Alternative: Free Mode (No Payments) ====================

def example_without_payments():
    """
    Example showing API calls that would fail without payment headers.
    This demonstrates the 402 Payment Required response.
    """
    print("🔒 Attempting to call API without payment...\n")

    client = httpx.Client(timeout=30.0)

    try:
        # Try to generate random bytes without payment
        response = client.post(
            f"{API_BASE_URL}/qrng/bytes",
            json={"length": 32, "format": "hex"},
        )

        if response.status_code == 402:
            error = response.json()
            print("❌ Payment Required (402)")
            print(f"   Error: {error.get('error')}")
            print(f"   Message: {error.get('message')}")
            print(f"   Price: {error.get('price')}")
            print(f"   Receiver: {error.get('receiver')}")
            print(f"   Network: {error.get('network')}")
            print(f"   Required Headers: {error.get('required_headers')}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        client.close()


# ==================== AI Agent Integration Example ====================

class AIAgentQRNGClient:
    """
    Example client designed for AI agents to use QRNG API

    AI agents can use this to:
    - Generate random seeds for ML model initialization
    - Create random sampling for data selection
    - Generate unique identifiers for sessions
    - Create cryptographic keys for secure communication
    """

    def __init__(self, api_url: str, private_key: str):
        self.client = QRNGClient(api_url, private_key)

    def get_random_seed_for_ml(self, bits: int = 256) -> int:
        """Get quantum random seed for ML model initialization"""
        result = self.client.generate_entropy(bits=bits)
        seed_hex = result['data']['entropy']['hex']
        return int(seed_hex, 16)

    def get_random_samples(self, count: int, min_val: int, max_val: int) -> list:
        """Get random sample indices for data selection"""
        result = self.client.generate_integers(count=count, min_value=min_val, max_value=max_val)
        return result['data']['random']

    def get_session_id(self) -> str:
        """Get unique session identifier"""
        result = self.client.generate_uuid()
        return result['data']['uuid']

    def get_crypto_key(self, key_size: int = 32) -> bytes:
        """Get cryptographic key for secure communication"""
        result = self.client.generate_bytes(length=key_size, format="hex")
        return bytes.fromhex(result['data']['random'])


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--no-payment-demo":
        example_without_payments()
    else:
        main()
