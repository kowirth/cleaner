#!/usr/bin/env python3
"""
MockMint - Simulated Cashu eCash Mint for Testing

This module provides a simulated Cashu mint that mimics the behavior of a real
eCash mint without requiring actual network connections or real value.
"""

import asyncio
import hashlib
import logging
import secrets
import time
from datetime import datetime
from typing import Dict, List, Optional


class BearerToken:
    """Represents a simulated Cashu bearer token."""
    
    def __init__(self, mint_id: str, amount: int, token_data: str, timestamp: float):
        self.mint_id = mint_id
        self.amount = amount
        self.token_data = token_data
        self.timestamp = timestamp
        self.token_id = hashlib.sha256(
            f"{mint_id}{amount}{token_data}{timestamp}".encode()
        ).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        """Convert token to dictionary representation."""
        return {
            'token_id': self.token_id,
            'mint_id': self.mint_id,
            'amount': self.amount,
            'token_data': self.token_data,
            'timestamp': self.timestamp,
            'created_at': datetime.fromtimestamp(self.timestamp).isoformat()
        }
    
    def __repr__(self) -> str:
        return f"BearerToken(id={self.token_id}, mint={self.mint_id[:8]}..., amount={self.amount})"


class MockMint:
    """
    Simulated Cashu eCash Mint.
    
    This class simulates a Cashu mint with the following capabilities:
    - Minting bearer tokens from input data
    - Redeeming tokens for new tokens
    - Network latency simulation
    - Comprehensive operation logging
    """
    
    _instance_counter = 0
    
    def __init__(self, name: Optional[str] = None, min_latency_ms: int = 50, max_latency_ms: int = 200):
        """
        Initialize a MockMint instance.
        
        Args:
            name: Optional name for the mint (auto-generated if not provided)
            min_latency_ms: Minimum simulated network latency in milliseconds
            max_latency_ms: Maximum simulated network latency in milliseconds
        """
        MockMint._instance_counter += 1
        self.mint_id = hashlib.sha256(
            f"{name or 'MockMint'}{MockMint._instance_counter}{time.time()}".encode()
        ).hexdigest()
        self.name = name or f"MockMint-{MockMint._instance_counter:02d}"
        self.min_latency = min_latency_ms / 1000.0
        self.max_latency = max_latency_ms / 1000.0
        self.logger = logging.getLogger(__name__)
        
        # Track issued and redeemed tokens
        self.issued_tokens: Dict[str, BearerToken] = {}
        self.redeemed_tokens: Dict[str, BearerToken] = {}
        
        # Statistics
        self.total_minted = 0
        self.total_redeemed = 0
        self.total_amount_minted = 0
        self.total_amount_redeemed = 0
        
        self.logger.info(
            f"[MINT_INIT] Initialized {self.name} | "
            f"mint_id={self.mint_id[:16]}... | "
            f"latency={self.min_latency*1000:.0f}-{self.max_latency*1000:.0f}ms"
        )
    
    async def _simulate_latency(self):
        """Simulate network latency with random delay."""
        latency = secrets.randbelow(int((self.max_latency - self.min_latency) * 1000)) / 1000.0
        latency += self.min_latency
        await asyncio.sleep(latency)
    
    async def mint_tokens(self, amount: int, source_data: Optional[str] = None) -> List[BearerToken]:
        """
        Mint new bearer tokens.
        
        Args:
            amount: Total amount to mint
            source_data: Optional source data identifier
            
        Returns:
            List of BearerToken objects
        """
        await self._simulate_latency()
        
        timestamp = time.time()
        token_data = secrets.token_hex(32)
        
        token = BearerToken(
            mint_id=self.mint_id,
            amount=amount,
            token_data=token_data,
            timestamp=timestamp
        )
        
        self.issued_tokens[token.token_id] = token
        self.total_minted += 1
        self.total_amount_minted += amount
        
        self.logger.info(
            f"[MINT_TOKENS] {self.name} | "
            f"token_id={token.token_id} | "
            f"amount={amount} | "
            f"source={source_data or 'N/A'} | "
            f"token_data={token_data[:16]}... | "
            f"timestamp={datetime.fromtimestamp(timestamp).isoformat()}"
        )
        
        return [token]
    
    async def redeem_tokens(self, tokens: List[BearerToken]) -> Dict:
        """
        Redeem bearer tokens.
        
        Args:
            tokens: List of BearerToken objects to redeem
            
        Returns:
            Dictionary with redemption details
        """
        await self._simulate_latency()
        
        total_amount = 0
        redeemed_token_ids = []
        
        for token in tokens:
            # Validate token (in mock, we accept any token from any mint)
            total_amount += token.amount
            redeemed_token_ids.append(token.token_id)
            
            # Mark as redeemed
            self.redeemed_tokens[token.token_id] = token
            self.total_redeemed += 1
            self.total_amount_redeemed += token.amount
            
            self.logger.info(
                f"[REDEEM_TOKEN] {self.name} | "
                f"token_id={token.token_id} | "
                f"original_mint={token.mint_id[:16]}... | "
                f"amount={token.amount} | "
                f"redemption_time={datetime.now().isoformat()}"
            )
        
        result = {
            'mint_id': self.mint_id,
            'mint_name': self.name,
            'redeemed_tokens': redeemed_token_ids,
            'total_amount': total_amount,
            'redemption_timestamp': time.time()
        }
        
        self.logger.info(
            f"[REDEEM_COMPLETE] {self.name} | "
            f"tokens_redeemed={len(tokens)} | "
            f"total_amount={total_amount}"
        )
        
        return result
    
    def get_stats(self) -> Dict:
        """Get mint statistics."""
        return {
            'mint_id': self.mint_id,
            'mint_name': self.name,
            'total_minted': self.total_minted,
            'total_redeemed': self.total_redeemed,
            'total_amount_minted': self.total_amount_minted,
            'total_amount_redeemed': self.total_amount_redeemed,
            'active_tokens': len(self.issued_tokens) - len(self.redeemed_tokens)
        }
    
    def __repr__(self) -> str:
        return f"MockMint(name={self.name}, id={self.mint_id[:8]}...)"


async def test_mock_mint():
    """Simple test function for MockMint."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n=== MockMint Test ===\n")
    
    # Create two mints
    mint_a = MockMint(name="TestMintA")
    mint_b = MockMint(name="TestMintB")
    
    # Mint tokens at Mint A
    print(f"Minting 1000 units at {mint_a.name}...")
    tokens = await mint_a.mint_tokens(1000, source_data="original_source")
    print(f"Minted: {tokens[0]}\n")
    
    # Redeem tokens at Mint B
    print(f"Redeeming tokens at {mint_b.name}...")
    redemption = await mint_b.redeem_tokens(tokens)
    print(f"Redemption result: {redemption}\n")
    
    # Mint new tokens at Mint B
    print(f"Minting new tokens at {mint_b.name}...")
    new_tokens = await mint_b.mint_tokens(1000)
    print(f"New tokens: {new_tokens[0]}\n")
    
    # Display stats
    print("=== Statistics ===")
    print(f"{mint_a.name}: {mint_a.get_stats()}")
    print(f"{mint_b.name}: {mint_b.get_stats()}")


if __name__ == "__main__":
    asyncio.run(test_mock_mint())
