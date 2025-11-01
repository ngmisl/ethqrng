#!/bin/bash

# QRNG API Server Launcher
# Quick start script for running the QRNG API server

set -e

echo "🌌 QRNG API Server Launcher"
echo "=============================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "✏️  Please edit .env and configure:"
    echo "   1. IBM_QUANTUM_TOKEN - Get from https://quantum.ibm.com/"
    echo "   2. X402_RECEIVER_ADDRESS - Your wallet address for receiving payments"
    echo "   3. X402_DEFAULT_NETWORK - Blockchain network (base, solana, etc)"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if IBM_QUANTUM_TOKEN is set
source .env
if [ -z "$IBM_QUANTUM_TOKEN" ] || [ "$IBM_QUANTUM_TOKEN" = "your_ibm_quantum_token_here" ]; then
    echo "❌ IBM_QUANTUM_TOKEN not configured in .env"
    echo "📖 Get your token from: https://quantum.ibm.com/"
    exit 1
fi

if [ -z "$X402_RECEIVER_ADDRESS" ] || [ "$X402_RECEIVER_ADDRESS" = "0xYourWalletAddressHere" ]; then
    echo "❌ X402_RECEIVER_ADDRESS not configured in .env"
    echo "💰 Set your wallet address to receive payments"
    exit 1
fi

echo "✅ Configuration loaded from .env"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Virtual environment not found"
    echo "🔨 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -e .

echo ""
echo "🚀 Starting QRNG API Server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the server
python qrng_api.py
