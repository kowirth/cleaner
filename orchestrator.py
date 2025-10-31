#!/usr/bin/env python3
"""
Digital Purgatory Protocol - Orchestrator

Main application for managing eCash token transmigration across multiple mints
to achieve transactional privacy through custody chain severance.
"""

import asyncio
import logging
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from mock_mint import BearerToken, MockMint


# Configure comprehensive logging
def setup_logging():
    """Configure verbose logging to dfir/ directory."""
    dfir_dir = Path("dfir")
    dfir_dir.mkdir(exist_ok=True)
    
    log_file = dfir_dir / "orchestrator.log"
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)


class DigitalPurgatoryOrchestrator:
    """
    Main orchestrator for the Digital Purgatory Protocol.
    
    Manages the transmigration of eCash tokens across multiple mints
    to sever the custody chain and achieve transactional privacy.
    """
    
    def __init__(self, num_hops: int = 10, num_mints: int = 15):
        """
        Initialize the orchestrator.
        
        Args:
            num_hops: Number of hops in the transmigration cycle
            num_mints: Number of mock mints to create in the vendor pool
        """
        self.logger = logging.getLogger(__name__)
        self.num_hops = num_hops
        self.num_mints = num_mints
        self.vendor_pool: List[MockMint] = []
        
        self.logger.info(
            f"[ORCHESTRATOR_INIT] Initializing Digital Purgatory Protocol | "
            f"hops={num_hops} | vendor_pool_size={num_mints}"
        )
    
    async def discover_vendors(self):
        """
        Discover and initialize vendor pool.
        
        In mock mode, this creates a pool of simulated MockMint instances.
        In production, this would discover real Cashu mints via Nostr relays.
        """
        self.logger.info(f"[VENDOR_DISCOVERY] Initiating vendor discovery for {self.num_mints} mints...")
        
        for i in range(self.num_mints):
            mint = MockMint(
                name=f"Vendor-{chr(65 + i % 26)}{i // 26 + 1}",
                min_latency_ms=30,
                max_latency_ms=150
            )
            self.vendor_pool.append(mint)
            self.logger.debug(
                f"[VENDOR_DISCOVERED] {mint.name} | mint_id={mint.mint_id[:16]}..."
            )
        
        self.logger.info(
            f"[VENDOR_DISCOVERY_COMPLETE] Discovered {len(self.vendor_pool)} vendors | "
            f"vendors=[{', '.join([m.name for m in self.vendor_pool[:5]])}...]"
        )
    
    def select_mint_for_hop(self, hop_number: int, exclude: Optional[List[str]] = None) -> MockMint:
        """
        Select a mint for a specific hop.
        
        Args:
            hop_number: Current hop number (for logging)
            exclude: List of mint IDs to exclude from selection
            
        Returns:
            Selected MockMint instance
        """
        exclude = exclude or []
        available_mints = [m for m in self.vendor_pool if m.mint_id not in exclude]
        
        if not available_mints:
            self.logger.warning("[MINT_SELECTION] No available mints, using full pool")
            available_mints = self.vendor_pool
        
        selected = random.choice(available_mints)
        self.logger.debug(
            f"[MINT_SELECTED] Hop {hop_number} | "
            f"mint={selected.name} | "
            f"mint_id={selected.mint_id[:16]}..."
        )
        
        return selected
    
    async def transmigration_initiation(self, original_data: int, source_id: str = "original_source") -> List[BearerToken]:
        """
        Initiate transmigration by minting tokens at the first vendor.
        
        Args:
            original_data: Amount to transmigrate
            source_id: Identifier for the original data source
            
        Returns:
            List of BearerToken objects from the first mint
        """
        self.logger.info(
            f"[TRANSMIGRATION_INIT] Starting transmigration | "
            f"amount={original_data} | source={source_id}"
        )
        
        # Select first mint
        first_mint = self.select_mint_for_hop(0)
        
        self.logger.info(
            f"[HOP_0_MINT] Minting at {first_mint.name} | "
            f"amount={original_data} | source={source_id}"
        )
        
        tokens = await first_mint.mint_tokens(original_data, source_data=source_id)
        
        self.logger.info(
            f"[HOP_0_COMPLETE] Initial tokens minted | "
            f"token_ids=[{', '.join([t.token_id for t in tokens])}] | "
            f"mint={first_mint.name}"
        )
        
        return tokens
    
    async def execute_cross_vendor_redemption(
        self,
        tokens: List[BearerToken],
        target_mint: MockMint,
        hop_number: int
    ) -> List[BearerToken]:
        """
        Execute cross-vendor redemption and re-minting.
        
        This is the critical operation that severs the custody chain:
        1. Redeem tokens at new mint (different from origin)
        2. Mint fresh tokens at the same mint
        
        Args:
            tokens: Tokens to redeem
            target_mint: Mint where tokens will be redeemed and new ones minted
            hop_number: Current hop number
            
        Returns:
            List of new BearerToken objects
        """
        original_mint_ids = [t.mint_id[:16] for t in tokens]
        total_amount = sum(t.amount for t in tokens)
        
        self.logger.info(
            f"[HOP_{hop_number}_REDEEM] Redeeming at {target_mint.name} | "
            f"tokens={len(tokens)} | "
            f"amount={total_amount} | "
            f"original_mints={original_mint_ids}"
        )
        
        # Redeem tokens at target mint
        redemption = await target_mint.redeem_tokens(tokens)
        
        self.logger.info(
            f"[HOP_{hop_number}_REDEMPTION_COMPLETE] "
            f"mint={target_mint.name} | "
            f"redeemed_amount={redemption['total_amount']}"
        )
        
        # Mint new tokens at the same mint
        self.logger.info(
            f"[HOP_{hop_number}_MINT] Minting fresh tokens at {target_mint.name} | "
            f"amount={redemption['total_amount']}"
        )
        
        new_tokens = await target_mint.mint_tokens(redemption['total_amount'])
        
        self.logger.info(
            f"[HOP_{hop_number}_COMPLETE] Custody chain severed | "
            f"old_tokens={[t.token_id for t in tokens]} | "
            f"new_tokens={[t.token_id for t in new_tokens]} | "
            f"mint={target_mint.name}"
        )
        
        return new_tokens
    
    async def iterative_obfuscation_loop(
        self,
        initial_amount: int,
        source_id: str = "source_data"
    ) -> List[BearerToken]:
        """
        Execute the full transmigration cycle with multiple hops.
        
        This performs the iterative obfuscation by:
        1. Minting tokens at first vendor
        2. For each hop: redeem at new vendor, mint fresh tokens
        3. Return final tokens after all hops
        
        Args:
            initial_amount: Amount to transmigrate
            source_id: Source data identifier
            
        Returns:
            Final BearerToken objects after all hops
        """
        self.logger.info(
            f"[OBFUSCATION_LOOP_START] Starting {self.num_hops}-hop transmigration | "
            f"amount={initial_amount} | source={source_id}"
        )
        
        start_time = datetime.now()
        
        # Hop 0: Initial minting
        current_tokens = await self.transmigration_initiation(initial_amount, source_id)
        previous_mint_id = current_tokens[0].mint_id
        
        # Hops 1 through N
        for hop in range(1, self.num_hops + 1):
            self.logger.info(f"[HOP_{hop}] Starting hop {hop}/{self.num_hops}")
            
            # Select a different mint from the previous one
            target_mint = self.select_mint_for_hop(hop, exclude=[previous_mint_id])
            
            # Execute cross-vendor redemption and minting
            current_tokens = await self.execute_cross_vendor_redemption(
                current_tokens,
                target_mint,
                hop
            )
            
            previous_mint_id = current_tokens[0].mint_id
            
            self.logger.info(
                f"[HOP_{hop}_STATUS] Hop complete | "
                f"tokens={len(current_tokens)} | "
                f"current_mint={target_mint.name}"
            )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.logger.info(
            f"[OBFUSCATION_LOOP_COMPLETE] Transmigration complete | "
            f"hops={self.num_hops} | "
            f"duration={duration:.2f}s | "
            f"final_tokens={[t.token_id for t in current_tokens]} | "
            f"final_mint={current_tokens[0].mint_id[:16]}..."
        )
        
        return current_tokens
    
    def get_vendor_statistics(self) -> dict:
        """Get statistics for all vendors in the pool."""
        stats = {
            'total_vendors': len(self.vendor_pool),
            'vendors': [mint.get_stats() for mint in self.vendor_pool]
        }
        return stats


async def main():
    """Main entry point for the orchestrator."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    logger = setup_logging()
    logger.info("=" * 80)
    logger.info("[STARTUP] Digital Purgatory Protocol - Orchestrator")
    logger.info("=" * 80)
    
    # Configuration
    num_hops = int(os.getenv("NUM_HOPS", "10"))
    num_mints = 15
    test_amount = 10000  # Test with 10,000 units
    
    logger.info(f"[CONFIG] Configuration loaded | hops={num_hops} | mints={num_mints}")
    
    # Initialize orchestrator
    orchestrator = DigitalPurgatoryOrchestrator(
        num_hops=num_hops,
        num_mints=num_mints
    )
    
    # Discover vendors
    await orchestrator.discover_vendors()
    
    # Execute transmigration
    logger.info(f"[EXECUTION] Starting transmigration test with {test_amount} units")
    final_tokens = await orchestrator.iterative_obfuscation_loop(
        test_amount,
        source_id="test_source_data"
    )
    
    # Display results
    logger.info("=" * 80)
    logger.info("[RESULTS] Transmigration Results")
    logger.info("=" * 80)
    logger.info(f"Final Tokens: {len(final_tokens)}")
    for token in final_tokens:
        logger.info(f"  - {token}")
    
    # Vendor statistics
    stats = orchestrator.get_vendor_statistics()
    logger.info(f"\nVendor Statistics: {stats['total_vendors']} vendors")
    
    logger.info("=" * 80)
    logger.info("[SHUTDOWN] Orchestrator execution complete")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
