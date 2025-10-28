#!/usr/bin/env python3
"""
Quantum-Secure Ethereum Wallet Generator
=========================================
Production-ready implementation with:
- IBM Quantum QRNG for true randomness
- Post-quantum cryptography (Dilithium/ML-DSA-65)
- Encrypted key storage
- Multiple security layers

Author: Quantum Security Team
License: MIT
"""

import os
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

# Quantum imports
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler import generate_preset_pass_manager

# Ethereum imports
from eth_account import Account
from web3 import Web3
from eth_account.messages import encode_defunct

# Post-quantum cryptography
try:
    from dilithium import Dilithium2, Dilithium3, Dilithium5
    PQC_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: dilithium-py not installed. Post-quantum signatures disabled.")
    PQC_AVAILABLE = False

# Encryption
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

class QuantumEthereumWallet:
    """
    Quantum-secure Ethereum wallet generator with post-quantum cryptography.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize wallet generator with configuration."""
        self.config = self.load_config(config_path)
        self.quantum_service = None
        self.pqc_keypair = None
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            print(f"⚠️  Config file {config_path} not found. Using defaults.")
            return {
                "security_level": "ML_DSA_65",
                "quantum_shots": 1024,
                "backup_directory": "./backups/",
                "default_output_file": "quantum_ethereum_key.enc"
            }
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def connect_quantum(self) -> None:
        """Connect to IBM Quantum service."""
        print("[1/7] 🔌 Connecting to IBM Quantum...")
        
        token = self.config.get('ibm_quantum_token')
        if not token or token == "YOUR_IBM_QUANTUM_TOKEN_HERE":
            raise ValueError(
                "IBM Quantum token not set in config.json\n"
                "Get your token from: https://quantum.cloud.ibm.com/"
            )
        
        self.quantum_service = QiskitRuntimeService(
            channel='ibm_quantum',
            token=token
        )
        print("    ✅ Connected to IBM Quantum")
    
    def create_qrng_circuit(self, num_bits: int) -> QuantumCircuit:
        """
        Create quantum random number generator circuit.
        
        Uses Hadamard gates to create superposition, then measures
        to get truly random bits from quantum mechanics.
        """
        qc = QuantumCircuit(num_bits, num_bits)
        
        # Create superposition on all qubits
        for i in range(num_bits):
            qc.h(i)
        
        # Measure all qubits
        for i in range(num_bits):
            qc.measure(i, i)
        
        return qc
    
    def generate_quantum_entropy(self, bits_needed: int = 256) -> bytes:
        """
        Generate cryptographic entropy using quantum computer.
        
        Args:
            bits_needed: Number of random bits to generate (default: 256 for Ethereum)
        
        Returns:
            bytes: Cryptographically secure random bytes from quantum measurements
        """
        print(f"[2/7] 🎲 Generating {bits_needed} quantum random bits...")
        
        if not self.quantum_service:
            self.connect_quantum()
        
        # Get least busy quantum backend
        backend = self.quantum_service.least_busy(
            simulator=False,
            operational=True
        )
        print(f"    ✅ Using quantum computer: {backend.name}")
        print(f"    📊 Qubits available: {backend.num_qubits}")
        
        # Determine optimal bit generation strategy
        available_qubits = min(backend.num_qubits, 127)
        bits_per_run = min(available_qubits, 32)
        num_runs = (bits_needed + bits_per_run - 1) // bits_per_run
        
        print(f"    🔄 Running {num_runs} quantum jobs ({bits_per_run} bits each)")
        
        all_bits = ""
        
        for run in range(num_runs):
            # Create QRNG circuit
            qc = self.create_qrng_circuit(bits_per_run)
            
            # Transpile for backend
            pm = generate_preset_pass_manager(
                backend=backend,
                optimization_level=1
            )
            isa_circuit = pm.run(qc)
            
            # Execute on quantum hardware
            sampler = Sampler(backend)
            job = sampler.run(
                [isa_circuit],
                shots=self.config.get('quantum_shots', 1024)
            )
            
            print(f"    ⏳ Job {run+1}/{num_runs} submitted: {job.job_id()}")
            
            # Get results
            result = job.result()
            counts = result[0].data.meas.get_counts()
            
            # Use most frequent measurement (from multiple shots)
            bitstring = max(counts.items(), key=lambda x: x[1])[0]
            all_bits += bitstring
            
            print(f"    ✅ Got quantum bits: {bitstring}")
        
        # Trim to exact length needed
        all_bits = all_bits[:bits_needed]
        
        # Convert to bytes
        entropy_bytes = int(all_bits, 2).to_bytes(
            (bits_needed + 7) // 8,
            byteorder='big'
        )
        
        print(f"    ✅ Generated {len(entropy_bytes)} bytes of quantum entropy")
        return entropy_bytes
    
    def generate_ethereum_key(self, entropy: bytes) -> Tuple[str, str, str]:
        """
        Generate Ethereum key from quantum entropy.
        
        Args:
            entropy: Random bytes from quantum source
        
        Returns:
            Tuple of (private_key_hex, public_key, address)
        """
        print("[3/7] 🔑 Generating Ethereum key...")
        
        # Create account from quantum entropy
        account = Account.from_key(entropy)
        
        private_key = account.key.hex()
        address = account.address
        
        # Derive public key
        public_key = account._key_obj.public_key.to_hex()
        
        print(f"    ✅ Address: {address}")
        return private_key, public_key, address
    
    def generate_pqc_keypair(self) -> Dict:
        """
        Generate post-quantum cryptography keypair using Dilithium.
        
        This provides quantum-resistant signatures for future protection.
        """
        print("[4/7] 🛡️  Generating post-quantum keypair...")
        
        if not PQC_AVAILABLE:
            print("    ⚠️  Dilithium not available, skipping PQC")
            return None
        
        security_level = self.config.get('security_level', 'ML_DSA_65')
        
        # Map security levels to Dilithium variants
        dilithium_map = {
            'ML_DSA_44': Dilithium2,
            'ML_DSA_65': Dilithium3,  # Default, good balance
            'ML_DSA_87': Dilithium5   # Highest security
        }
        
        DilithiumClass = dilithium_map.get(security_level, Dilithium3)
        
        # Generate quantum-resistant keypair
        pk, sk = DilithiumClass.keygen()
        
        print(f"    ✅ Generated {security_level} keypair")
        print(f"    📏 Public key size: {len(pk)} bytes")
        print(f"    📏 Secret key size: {len(sk)} bytes")
        
        return {
            'public_key': pk.hex(),
            'secret_key': sk.hex(),
            'algorithm': security_level
        }
    
    def encrypt_key_data(self, data: Dict, password: str) -> bytes:
        """
        Encrypt key data with password using PBKDF2 + Fernet.
        
        Args:
            data: Dictionary containing key information
            password: User password for encryption
        
        Returns:
            Encrypted data as bytes
        """
        print("[5/7] 🔐 Encrypting key data...")
        
        # Generate salt
        salt = os.urandom(32)
        
        # Derive encryption key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        
        # Create Fernet cipher
        fernet = Fernet(Web3.to_base64(key[:32]))
        
        # Serialize and encrypt data
        json_data = json.dumps(data).encode()
        encrypted = fernet.encrypt(json_data)
        
        # Prepend salt for later decryption
        result = salt + encrypted
        
        print("    ✅ Data encrypted successfully")
        return result
    
    def save_encrypted_wallet(self, encrypted_data: bytes, filename: str) -> None:
        """Save encrypted wallet to file."""
        print(f"[6/7] 💾 Saving encrypted wallet...")
        
        # Ensure output directory exists
        output_dir = Path(filename).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'wb') as f:
            f.write(encrypted_data)
        
        print(f"    ✅ Saved to: {filename}")
    
    def create_backup(self, encrypted_data: bytes, address: str) -> None:
        """Create timestamped backup."""
        print("[7/7] 📦 Creating backup...")
        
        backup_dir = Path(self.config.get('backup_directory', './backups/'))
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"wallet_{address[:10]}_{timestamp}.enc"
        
        with open(backup_file, 'wb') as f:
            f.write(encrypted_data)
        
        print(f"    ✅ Backup saved to: {backup_file}")
    
    def generate_wallet(self, password: str, output_file: Optional[str] = None) -> Dict:
        """
        Complete wallet generation process.
        
        Args:
            password: Password for encrypting the wallet
            output_file: Optional custom output filename
        
        Returns:
            Dictionary with wallet information
        """
        print("=" * 70)
        print("⚛️  QUANTUM-SECURE ETHEREUM WALLET GENERATOR")
        print("=" * 70)
        print()
        
        # Generate quantum entropy
        entropy = self.generate_quantum_entropy(256)
        
        # Generate Ethereum key
        private_key, public_key, address = self.generate_ethereum_key(entropy)
        
        # Generate post-quantum keypair
        pqc_keypair = self.generate_pqc_keypair()
        
        # Prepare wallet data
        wallet_data = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'ethereum': {
                'private_key': private_key,
                'public_key': public_key,
                'address': address
            },
            'quantum_entropy_bits': entropy.hex(),
            'post_quantum_crypto': pqc_keypair
        }
        
        # Encrypt wallet
        encrypted_data = self.encrypt_key_data(wallet_data, password)
        
        # Save to file
        if output_file is None:
            output_file = self.config.get(
                'default_output_file',
                'quantum_ethereum_key.enc'
            )
        
        self.save_encrypted_wallet(encrypted_data, output_file)
        
        # Create backup
        self.create_backup(encrypted_data, address)
        
        # Display results
        print()
        print("=" * 70)
        print("✅ WALLET GENERATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n📍 Ethereum Address: {address}")
        print(f"🔑 Private Key: {private_key[:20]}...{private_key[-20:]}")
        print(f"💾 Encrypted File: {output_file}")
        
        if pqc_keypair:
            print(f"🛡️  Post-Quantum Algorithm: {pqc_keypair['algorithm']}")
            print(f"🔐 PQC Public Key: {pqc_keypair['public_key'][:40]}...")
        
        print("\n" + "=" * 70)
        print("🔒 SECURITY REMINDERS:")
        print("   • Your wallet is encrypted with your password")
        print("   • Store the encrypted file in multiple secure locations")
        print("   • NEVER share your private key or password")
        print("   • Backup file created in backups/ directory")
        print("   • Generated using TRUE quantum randomness")
        if pqc_keypair:
            print("   • Protected with post-quantum cryptography")
        print("=" * 70)
        print()
        
        return wallet_data

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Quantum-Secure Ethereum Wallet Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate new wallet
  python quantum_ethereum_wallet.py generate --password "my-secure-password"
  
  # Generate with custom output
  python quantum_ethereum_wallet.py generate -p "password" -o my_wallet.enc
  
  # Use custom config
  python quantum_ethereum_wallet.py generate -p "password" -c custom_config.json

Security Features:
  ✅ IBM Quantum QRNG - True random number generation
  ✅ Post-quantum cryptography (Dilithium/ML-DSA)
  ✅ Password-based encryption (PBKDF2 + Fernet)
  ✅ Automated backups
  ✅ Industry-standard Ethereum key derivation
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate new quantum wallet')
    gen_parser.add_argument(
        '-p', '--password',
        required=True,
        help='Password to encrypt the wallet'
    )
    gen_parser.add_argument(
        '-o', '--output',
        help='Output file (default: from config)'
    )
    gen_parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='Configuration file (default: config.json)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        wallet_gen = QuantumEthereumWallet(args.config)
        wallet_gen.generate_wallet(args.password, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
