# Digital Purgatory Protocol

**eCash Transmigration System for Transactional Privacy**

A Python-based implementation of a privacy-focused eCash token transmigration system that achieves transaction anonymity through multi-hop custody chain severance across independent Cashu mints.

---

## 🎯 Overview

The Digital Purgatory Protocol implements a **10-hop transmigration cycle** that systematically severs the custody chain for digital bearer tokens. By rapidly converting tokens across multiple independent mint vendors, the system creates an untraceable path between source and destination, effectively "reincarnating" the digital value in a pristine, anonymous form.

### Core Concept

```
Original Source → Mint A → Redeem at Mint B → Mint B → Redeem at Mint C → ... → Final Clean Token
                   ↓                              ↓                              ↓
              Custody Severed              Custody Severed              Custody Severed
```

Each hop in the chain:
1. **Redeems** tokens at a new, independent mint (different from origin)
2. **Mints** fresh tokens at that same mint
3. **Passes** the new tokens to the next hop

After 10 hops, the final token has **no traceable relationship** to the original source.

---

## 🏗️ Architecture

### Components

1. **MockMint** (`mock_mint.py`)
   - Simulated Cashu eCash mint
   - Implements token minting and redemption
   - Simulates network latency (50-200ms)
   - Comprehensive operation logging

2. **Orchestrator** (`orchestrator.py`)
   - Main transmigration engine
   - Vendor pool management (15+ simulated mints)
   - 10-hop iterative obfuscation loop
   - Verbose logging to `dfir/` directory

3. **Test Suite** (`test_transmigration.py`)
   - 6 comprehensive test suites
   - Validates custody chain severance
   - Verifies logging integrity
   - Performance benchmarking

### Privacy Mechanism

The privacy guarantee comes from the **cross-vendor redemption** pattern:

- **Mint A** issues tokens but has no knowledge of where they'll be redeemed
- **Mint B** redeems tokens from Mint A but doesn't know they originated there
- **Mint B** issues fresh tokens with no relationship to the redeemed ones
- After 10 such hops, the provenance trail is effectively obliterated

### Mock vs. Real Mints

**Current Implementation (Mock Mode):**
- Simulated mints for testing and development
- No real network connections required
- No real value at risk
- Instant feedback and iteration

**Future Implementation (Production Mode):**
- Real Cashu mints discovered via Nostr relays (NIP-60/NIP-61)
- Actual eCash token operations
- Tor integration for network anonymity
- Real-world transactional privacy

---

## 📋 Prerequisites

- **Python 3.10+** (tested with Python 3.14)
- **Git**
- **Internet connection** (for package installation only)

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/kowirth/ecashCleaner
cd ecashCleaner
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies installed:
- `aiohttp` - Asynchronous HTTP client/server
- `python-dotenv` - Environment variable management

### 4. Configure Environment (Optional)

```bash
cp .env.example .env
```

Edit `.env` to customize:
- `NUM_HOPS` - Number of transmigration hops (default: 10)
- `MOCK_MODE` - Enable/disable mock mode (default: true)

### 5. Run Tests

```bash
python test_transmigration.py
```

Expected output:
```
================================================================================
DIGITAL PURGATORY PROTOCOL - COMPREHENSIVE TEST SUITE
================================================================================
Started at: 2025-10-31T04:36:15

[TEST 1] Testing MockMint basic operations...
[TEST 2] Testing vendor discovery...
[TEST 3] Testing single hop transmigration...
[TEST 4] Testing full 10-hop transmigration cycle...
[TEST 5] Testing custody chain severance verification...
[TEST 6] Testing logging verification...

================================================================================
OVERALL: 22/22 tests passed
Success Rate: 100.0%
✓ ALL TESTS PASSED!
================================================================================
```

---

## 💻 Usage

### Run the Orchestrator

```bash
python orchestrator.py
```

This will:
1. Initialize 15 simulated mint vendors
2. Execute a 10-hop transmigration with 10,000 test units
3. Log all operations to `dfir/orchestrator.log`
4. Display final token results

### Run Individual MockMint Test

```bash
python mock_mint.py
```

### View Logs

```bash
cat dfir/orchestrator.log
```

Or for real-time monitoring:

```bash
tail -f dfir/orchestrator.log
```

---

## 📊 Technical Details

### Token Structure

Each `BearerToken` contains:

```python
{
    'token_id': str,        # Unique 16-char identifier
    'mint_id': str,         # Mint that issued this token (64-char hex)
    'amount': int,          # Value in units
    'token_data': str,      # Random 64-char hex data
    'timestamp': float,     # Unix timestamp of creation
    'created_at': str       # ISO 8601 datetime
}
```

### Hop Selection Algorithm

```python
def select_mint_for_hop(hop_number, exclude=[previous_mint_id]):
    available_mints = [m for m in vendor_pool if m.mint_id not in exclude]
    return random.choice(available_mints)
```

This ensures each hop uses a **different mint** from the previous one, maximizing the obfuscation effect.

### Logging System

All operations are logged to `dfir/orchestrator.log` with verbose detail:

```
2025-10-31 04:36:15 - orchestrator - INFO - [ORCHESTRATOR_INIT] Initializing Digital Purgatory Protocol | hops=10 | vendor_pool_size=15
2025-10-31 04:36:15 - orchestrator - INFO - [VENDOR_DISCOVERY] Initiating vendor discovery for 15 mints...
2025-10-31 04:36:15 - mock_mint - INFO - [MINT_INIT] Initialized Vendor-A1 | mint_id=a3f7e9c2... | latency=30-150ms
...
2025-10-31 04:36:16 - mock_mint - INFO - [MINT_TOKENS] Vendor-A1 | token_id=f8e4c3a1 | amount=10000 | source=test_source_data
2025-10-31 04:36:16 - orchestrator - INFO - [HOP_1] Starting hop 1/10
2025-10-31 04:36:16 - mock_mint - INFO - [REDEEM_TOKEN] Vendor-B2 | token_id=f8e4c3a1 | amount=10000
2025-10-31 04:36:16 - mock_mint - INFO - [MINT_TOKENS] Vendor-B2 | token_id=d9a2c7f5 | amount=10000
...
```

Log categories:
- `[ORCHESTRATOR_INIT]` - Orchestrator initialization
- `[VENDOR_DISCOVERY]` - Mint discovery operations
- `[HOP_N]` - Hop execution (N = 0-10)
- `[MINT_TOKENS]` - Token minting operations
- `[REDEEM_TOKEN]` - Token redemption operations
- `[CUSTODY_CHAIN_SEVERED]` - Custody severance confirmations

---

## 🔒 Security Considerations

### Privacy Guarantees

**What This System Provides:**
- ✅ Severs custody chain between source and destination
- ✅ No single mint knows the full transaction path
- ✅ Final tokens are cryptographically unrelated to originals
- ✅ Amount is preserved while provenance is obliterated

**What This System Does NOT Provide (in mock mode):**
- ❌ Network-level anonymity (no Tor integration yet)
- ❌ Protection against timing analysis attacks
- ❌ Real-world transactional value
- ❌ Legal protection in jurisdictions where this is prohibited

### Limitations of Mock System

The current mock implementation is **for testing and development only**:

- Simulated mints are all in-process (not independent entities)
- No real cryptographic validation of tokens
- No actual network communication
- Deterministic behavior (for testing reproducibility)

### Production Considerations

For real-world deployment, you would need:

1. **Real Cashu Mints**: Connect to actual independent mint services
2. **Nostr Integration**: Discover mints via decentralized Nostr relays
3. **Tor/VPN**: Route all network traffic through anonymity networks
4. **Timing Randomization**: Add random delays to prevent timing correlation
5. **Amount Splitting**: Break amounts into random denominations
6. **Legal Compliance**: Ensure compliance with local regulations

---

## 🛣️ Roadmap

### Phase 1: Foundation (✅ Complete)
- [x] MockMint implementation
- [x] Orchestrator with 10-hop logic
- [x] Comprehensive test suite
- [x] Verbose logging system
- [x] Documentation

### Phase 2: Real Mint Integration (Future)
- [ ] Cashu SDK integration
- [ ] Nostr relay communication (NIP-60/NIP-61)
- [ ] Dynamic mint discovery
- [ ] Real token operations
- [ ] Error handling for network failures

### Phase 3: Enhanced Privacy (Future)
- [ ] Tor/SOCKS5 proxy integration
- [ ] Timing attack mitigation
- [ ] Amount denomination splitting
- [ ] Multi-path routing
- [ ] Decoy traffic generation

### Phase 4: Production Hardening (Future)
- [ ] Rate limiting
- [ ] Mint reputation scoring
- [ ] Fallback mechanisms
- [ ] Monitoring and alerting
- [ ] Audit trail (optional)

---

## 📁 Project Structure

```
ecashCleaner/
├── dfir/                       # Digital Forensics logs
│   └── orchestrator.log        # Verbose operation logs
├── mock_mint.py                # Simulated Cashu mint implementation
├── orchestrator.py             # Main transmigration orchestrator
├── test_transmigration.py      # Comprehensive test suite
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
└── venv/                       # Virtual environment (not in repo)
```

---

## 🧪 Test Results

The test suite validates:

1. **MockMint Basic Operations**
   - Token minting
   - Token redemption
   - Statistics tracking

2. **Vendor Discovery**
   - Pool size verification
   - Mint uniqueness
   - Naming conventions

3. **Single Hop Transmigration**
   - Mint A → Mint B flow
   - Custody chain severance
   - Amount preservation

4. **Full 10-Hop Cycle**
   - Complete transmigration
   - All hops executed
   - Performance metrics

5. **Custody Chain Severance**
   - Token ID uniqueness
   - Mint ID changes
   - Timestamp freshness

6. **Logging Verification**
   - Log file existence
   - Key operation logging
   - Log volume metrics

---

## 🤝 Contributing

This is a research and development project. Contributions, issues, and feature requests are welcome.

**Areas for contribution:**
- Real Cashu mint integration
- Nostr relay implementation
- Privacy enhancement techniques
- Performance optimization
- Security auditing

---

## ⚖️ Legal Disclaimer

This software is provided for **educational and research purposes only**. The authors and contributors:

- Do NOT encourage or endorse illegal activities
- Do NOT provide any guarantees of anonymity or privacy
- Do NOT accept liability for misuse of this software
- Do NOT provide legal advice regarding cryptocurrency or privacy tools

**Users are solely responsible for:**
- Compliance with local laws and regulations
- Understanding the risks of cryptocurrency operations
- Securing their own systems and data
- Any consequences of using this software

In many jurisdictions, using privacy-enhancing technologies for financial transactions may have legal implications. Consult with legal counsel before deploying this system with real funds.

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🔗 References

- [Cashu Protocol](https://docs.cashu.space/) - eCash implementation specification
- [Nostr Protocol](https://github.com/nostr-protocol/nips) - Decentralized relay network
- [NIP-60](https://github.com/nostr-protocol/nips/blob/master/60.md) - Cashu Wallet
- [NIP-61](https://github.com/nostr-protocol/nips/blob/master/61.md) - Cashu Mint Discovery

---

## 📧 Contact

Project Link: [https://github.com/kowirth/ecashCleaner](https://github.com/kowirth/ecashCleaner)

---

**Built with privacy in mind. Use responsibly.**
