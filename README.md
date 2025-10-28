# Quantum Ethereum Wallet Generator

**ULTRA-SECURE Ethereum wallet generation using IBM Quantum computers with enhanced entropy mixing**

This project generates Ethereum wallets using quantum random number generation (QRNG) from IBM Quantum computers, combined with additional security layers to ensure that even IBM Quantum cannot derive your private keys.

## Features

- **Quantum Random Number Generation**: Uses real IBM Quantum hardware for true randomness
- **Defense-in-Depth Security**: Multiple entropy sources protect against quantum provider compromise
- **Zero-Knowledge Design**: IBM Quantum can observe random bits but cannot derive your private key
- **HKDF Key Derivation**: Cryptographically mixes multiple entropy sources
- **Password-Encrypted Storage**: Wallets are encrypted with PBKDF2 before saving
- **Cryptographic Proof**: Each wallet includes proof of entropy mixing
- **Air-Gap Compatible**: Can be run offline after quantum entropy generation

## Security Model

This implementation assumes that **IBM Quantum can observe** the random bits they generate, and provides additional security layers to prevent key derivation even under this assumption.

### Three-Layer Entropy Mixing

```
1. Quantum Entropy (256 bits) ê IBM CAN see this
2. OS Entropy (256 bits)      ê IBM CANNOT see this
3. User Salt (256 bits)       ê IBM CANNOT see this

          ì
   HKDF-SHA256 (one-way)
          ì
   Ethereum Private Key ê IBM CANNOT derive this
```

### Security Guarantees

Even if IBM Quantum:
-  Stores all quantum measurement results
-  Attempts to correlate with blockchain addresses
-  Has unlimited computational resources

They **CANNOT** derive your private key because:
- They don't have access to your OS entropy (generated locally)
- They don't have access to your user salt (generated locally)
- HKDF-SHA256 is a cryptographically secure one-way function
- The combination of all three entropy sources is required

## Prerequisites

- Python 3.12.4 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- IBM Quantum account (free at [quantum.ibm.com](https://quantum.ibm.com))
- IBM Quantum API token

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ethqrng
   ```

2. **Install dependencies with uv:**
   ```bash
   uv sync
   ```

3. **Set up configuration:**
   ```bash
   cp .env.example .env
   cp config.json.example config.json
   ```

4. **Edit `.env` file with your credentials:**
   ```bash
   IBM_QUANTUM_TOKEN=your_ibm_quantum_token_here
   WALLET_PASSWORD=your_secure_password_here
   ```

   Get your IBM Quantum token from: https://quantum.ibm.com/account

## Configuration

### Environment Variables (`.env`)

```env
# Required: Your IBM Quantum API token
IBM_QUANTUM_TOKEN=your_token_here

# Optional: Wallet encryption password (can also pass via CLI)
WALLET_PASSWORD=your_secure_password
```

### Configuration File (`config.json`)

```json
{
  "ibm_quantum_token": "YOUR_TOKEN",
  "security_level": "MAXIMUM",
  "entropy_mixing": true,
  "quantum_shots": 1024
}
```

**Note:** Environment variables take precedence over `config.json` values.

## Usage

### Basic Usage

```bash
# With password from environment variable
uv run python main.py

# With password from command line
uv run python main.py -p "YourSecurePassword123!"

# With custom config file
uv run python main.py -c custom_config.json

# With user-provided salt (hex string)
uv run python main.py -p "password" --user-salt "0123456789abcdef..."
```

### Example Output

```
======================================================================
õ  ULTRA-SECURE QUANTUM ETHEREUM WALLET GENERATOR
======================================================================

= Security Model: Defense Against IBM Observation
Even if IBM Quantum stores your random bits,
they cannot derive your private key.

[1/8] <≤ Generating quantum entropy from IBM Quantum...
     Using: ibm_brisbane
    õ  Quantum chunk 1/8: 10110101...
    ...
     Generated 32 bytes quantum entropy
    †  Note: IBM Quantum CAN see these bits

[2/8] = Generating OS entropy (invisible to IBM)...
     Generated 32 bytes OS entropy
    = This entropy is LOCAL ONLY (IBM cannot see)

[3/8] = Mixing entropy sources with HKDF...
    =  Total entropy: 96 bytes
       - Quantum: 32 bytes (IBM can see)
       - OS:      32 bytes (IBM CANNOT see)
       - Salt:    32 bytes (IBM CANNOT see)
     Entropy mixed with HKDF-SHA256
    ° IBM cannot derive this even with quantum entropy!

[4/8] = Deriving Ethereum key (local only)...
     Ethereum address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
    = Private key derived (IBM cannot compute this)

[5/8] =·  Creating security proof...
[6/8] = Encrypting wallet...
[7/8] =æ Saving encrypted wallet...
[8/8] =Ê Creating backup...

======================================================================
 ULTRA-SECURE WALLET GENERATED!
======================================================================

=Õ Ethereum Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
= Private Key: 0x1234567890abcdef...
=æ Encrypted File: quantum_wallet_enhanced.enc
```

## Output Files

The wallet generator creates:

1. **`quantum_wallet_enhanced.enc`** - Main encrypted wallet file
2. **`backup_wallet_<address>_<timestamp>.enc`** - Timestamped backup

### Wallet File Contents

Each encrypted wallet contains:

```json
{
  "version": "2.0-enhanced-security",
  "created": "2025-10-28T...",
  "ethereum": {
    "private_key": "0x...",
    "public_key": "0x...",
    "address": "0x..."
  },
  "security": {
    "quantum_entropy_bytes": "...",
    "user_salt": "...",
    "proof": {
      "quantum_entropy_sha256": "...",
      "os_entropy_sha256": "...",
      "user_salt_sha256": "...",
      "combined_sha256": "...",
      "entropy_sources": 3
    },
    "entropy_mixing": "HKDF-SHA256",
    "note": "IBM Quantum cannot derive private key from quantum entropy alone"
  }
}
```

## How It Works

### 1. Quantum Entropy Generation
- Creates quantum circuit with 32 qubits in superposition (Hadamard gates)
- Measures on real IBM Quantum hardware (not simulator)
- Collects 256 bits of quantum random data
- **Note:** IBM Quantum can observe these measurements

### 2. OS Entropy Generation
- Generates cryptographic random bytes using Python's `secrets` module
- Uses system entropy sources (`/dev/urandom` on Unix, `CryptGenRandom` on Windows)
- This entropy is generated **locally** and invisible to IBM

### 3. Entropy Mixing with HKDF
- Concatenates: `quantum_entropy || os_entropy || user_salt`
- Applies HKDF-SHA256 key derivation function
- Creates 256-bit key material
- This is a **one-way function** - cannot be reversed

### 4. Ethereum Key Derivation
- Uses `eth_account` library to create Ethereum account
- Derives private key, public key, and address
- All operations happen **locally**

### 5. Encryption & Storage
- Encrypts wallet data with password using PBKDF2 + Fernet
- Saves encrypted wallet to disk
- Creates timestamped backup

## Security Considerations

###  DO

- **Store your password securely** - Without it, you cannot decrypt your wallet
- **Keep multiple backups** - Store encrypted wallet files in different locations
- **Use a strong password** - 20+ characters, mixed case, numbers, symbols
- **Keep your `.env` file secure** - Never commit it to version control
- **Verify wallet address** - Always test with small amounts first

### L DON'T

- **Never commit `.env` or `config.json`** - They contain sensitive credentials
- **Never share your private key** - Anyone with it can steal your funds
- **Never commit `.enc` files** - Encrypted wallets should not be in version control
- **Don't use weak passwords** - Brute-force attacks are real
- **Don't skip backups** - Hardware failures happen

## Testing

Before using this wallet for real funds:

1. Generate a test wallet
2. Import the private key into MetaMask or another wallet
3. Send a small test transaction (on testnet or with minimal mainnet ETH)
4. Verify everything works correctly
5. Only then use for larger amounts

## IBM Quantum Setup

1. **Create IBM Quantum account:** https://quantum.ibm.com
2. **Get your API token:**
   - Log in to IBM Quantum
   - Go to Account settings
   - Copy your API token
3. **Choose quantum backend:**
   - The script automatically selects the least busy quantum computer
   - You can see which device was used in the output

## Dependencies

- **qiskit** - IBM's quantum computing framework
- **qiskit-ibm-runtime** - IBM Quantum cloud access
- **eth-account** - Ethereum account management
- **web3** - Ethereum blockchain interaction
- **cryptography** - HKDF, PBKDF2, and Fernet encryption
- **python-dotenv** - Environment variable management

## FAQ

### Q: Is this really secure?

**A:** Yes, if used correctly. The multi-layer entropy mixing ensures that even if IBM Quantum is compromised, your private key remains secure. However, you must:
- Use a strong password
- Keep your encrypted wallet files secure
- Never share your private key

### Q: Why use quantum random numbers if we don't trust IBM?

**A:** Quantum random numbers provide true, hardware-based randomness that's superior to pseudo-random number generators. By mixing quantum entropy with local OS entropy and a user salt, we get the best of both worlds: quantum randomness + zero-trust security.

### Q: Can I use this offline (air-gapped)?

**A:** Partially. You need internet connection to:
1. Generate quantum entropy (requires IBM Quantum cloud access)

After quantum entropy generation, you could theoretically disconnect and complete the process offline. However, the initial quantum measurement requires cloud access.

### Q: What if IBM Quantum shuts down?

**A:** Your wallet is independent of IBM Quantum after generation. The quantum entropy is just one ingredient in the mixing process. Your private key and wallet will continue to work normally.

### Q: How is this different from other wallet generators?

**A:** Most wallet generators use only pseudo-random number generators (PRNGs). This project uses:
- True quantum randomness (non-deterministic)
- Multiple independent entropy sources
- Cryptographic mixing (HKDF)
- Provable security against quantum provider compromise

## Disclaimer

**† IMPORTANT SECURITY NOTICE**

- This software is provided "AS IS" without warranty of any kind
- The authors are not responsible for any loss of funds
- Cryptocurrency wallets involve significant responsibility
- Always test with small amounts first
- Keep secure backups of your encrypted wallet files
- Never share your private keys or passwords
- Understand the risks before using with real funds

## License

This project is for educational and research purposes. Use at your own risk.

## Contributing

Contributions welcome! Please:
- Review the security model before proposing changes
- Include tests for new features
- Follow Python best practices
- Document security implications

## Support

For issues or questions:
- Open an issue on GitHub
- Review the security model in `SECURITY_ANALYSIS.md`
- Check IBM Quantum documentation for quantum-specific questions

---

**Built with quantum randomness and cryptographic rigor** õ=
