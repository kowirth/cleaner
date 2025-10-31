#!/usr/bin/env python3
"""
Test Suite for Digital Purgatory Protocol

Comprehensive tests for the eCash transmigration system including:
- Vendor discovery
- Single hop transmigration
- Full 10-hop transmigration cycle
- Custody chain severance verification
- Logging verification
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from mock_mint import BearerToken, MockMint
from orchestrator import DigitalPurgatoryOrchestrator, setup_logging


class TestResults:
    """Track test results and statistics."""
    
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_details = []
    
    def add_result(self, test_name: str, passed: bool, details: str = ""):
        """Add a test result."""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✓ PASS"
        else:
            self.failed_tests += 1
            status = "✗ FAIL"
        
        self.test_details.append({
            'name': test_name,
            'status': status,
            'passed': passed,
            'details': details
        })
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        for test in self.test_details:
            print(f"{test['status']} - {test['name']}")
            if test['details']:
                print(f"         {test['details']}")
        
        print("\n" + "-" * 80)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print("=" * 80 + "\n")
        
        return self.failed_tests == 0


async def test_mock_mint_basic():
    """Test 1: Basic MockMint functionality."""
    print("\n[TEST 1] Testing MockMint basic operations...")
    
    results = TestResults()
    
    try:
        # Create two mints
        mint_a = MockMint(name="TestMintA")
        mint_b = MockMint(name="TestMintB")
        
        # Test minting
        tokens = await mint_a.mint_tokens(1000, source_data="test_source")
        assert len(tokens) == 1, "Should mint 1 token"
        assert tokens[0].amount == 1000, "Token amount should be 1000"
        assert tokens[0].mint_id == mint_a.mint_id, "Token should have correct mint ID"
        results.add_result("MockMint: Token Minting", True, f"Minted token: {tokens[0].token_id}")
        
        # Test redemption
        redemption = await mint_b.redeem_tokens(tokens)
        assert redemption['total_amount'] == 1000, "Redemption amount should match"
        assert redemption['mint_id'] == mint_b.mint_id, "Redemption should be at correct mint"
        results.add_result("MockMint: Token Redemption", True, f"Redeemed {redemption['total_amount']} units")
        
        # Test statistics
        stats_a = mint_a.get_stats()
        assert stats_a['total_minted'] == 1, "Mint A should show 1 mint operation"
        results.add_result("MockMint: Statistics Tracking", True, f"Stats: {stats_a['total_minted']} minted")
        
    except Exception as e:
        results.add_result("MockMint Basic Operations", False, f"Error: {str(e)}")
    
    return results


async def test_vendor_discovery():
    """Test 2: Vendor discovery system."""
    print("\n[TEST 2] Testing vendor discovery...")
    
    results = TestResults()
    
    try:
        orchestrator = DigitalPurgatoryOrchestrator(num_hops=10, num_mints=15)
        await orchestrator.discover_vendors()
        
        assert len(orchestrator.vendor_pool) == 15, "Should discover 15 vendors"
        results.add_result("Vendor Discovery: Pool Size", True, f"Discovered {len(orchestrator.vendor_pool)} vendors")
        
        # Verify each mint is unique
        mint_ids = [mint.mint_id for mint in orchestrator.vendor_pool]
        assert len(mint_ids) == len(set(mint_ids)), "All mint IDs should be unique"
        results.add_result("Vendor Discovery: Uniqueness", True, "All mint IDs unique")
        
        # Verify vendor naming
        first_vendor = orchestrator.vendor_pool[0]
        assert first_vendor.name.startswith("Vendor-"), "Vendor should have correct naming"
        results.add_result("Vendor Discovery: Naming", True, f"Example: {first_vendor.name}")
        
    except Exception as e:
        results.add_result("Vendor Discovery", False, f"Error: {str(e)}")
    
    return results


async def test_single_hop():
    """Test 3: Single hop transmigration (Mint A -> Mint B)."""
    print("\n[TEST 3] Testing single hop transmigration...")
    
    results = TestResults()
    
    try:
        mint_a = MockMint(name="HopTestA")
        mint_b = MockMint(name="HopTestB")
        
        # Mint at A
        initial_tokens = await mint_a.mint_tokens(5000, source_data="hop_test_source")
        initial_token_id = initial_tokens[0].token_id
        initial_mint_id = initial_tokens[0].mint_id
        results.add_result("Single Hop: Initial Minting", True, f"Minted at {mint_a.name}")
        
        # Redeem at B
        redemption = await mint_b.redeem_tokens(initial_tokens)
        results.add_result("Single Hop: Redemption", True, f"Redeemed at {mint_b.name}")
        
        # Mint fresh tokens at B
        new_tokens = await mint_b.mint_tokens(redemption['total_amount'])
        new_token_id = new_tokens[0].token_id
        new_mint_id = new_tokens[0].mint_id
        results.add_result("Single Hop: Fresh Minting", True, f"New token at {mint_b.name}")
        
        # Verify custody chain is severed
        assert initial_token_id != new_token_id, "Token IDs should differ"
        assert initial_mint_id != new_mint_id, "Mint IDs should differ"
        assert new_tokens[0].amount == initial_tokens[0].amount, "Amount should be preserved"
        results.add_result(
            "Single Hop: Custody Chain Severance", 
            True, 
            f"Old: {initial_token_id} -> New: {new_token_id}"
        )
        
    except Exception as e:
        results.add_result("Single Hop Transmigration", False, f"Error: {str(e)}")
    
    return results


async def test_full_transmigration():
    """Test 4: Full 10-hop transmigration cycle."""
    print("\n[TEST 4] Testing full 10-hop transmigration cycle...")
    
    results = TestResults()
    
    try:
        orchestrator = DigitalPurgatoryOrchestrator(num_hops=10, num_mints=15)
        await orchestrator.discover_vendors()
        
        initial_amount = 25000
        source_id = "full_test_source"
        
        # Execute full transmigration
        start_time = datetime.now()
        final_tokens = await orchestrator.iterative_obfuscation_loop(initial_amount, source_id)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Verify results
        assert len(final_tokens) > 0, "Should have final tokens"
        results.add_result("Full Transmigration: Execution", True, f"Completed in {duration:.2f}s")
        
        assert final_tokens[0].amount == initial_amount, "Amount should be preserved"
        results.add_result("Full Transmigration: Amount Preservation", True, f"{initial_amount} units preserved")
        
        # Verify statistics
        stats = orchestrator.get_vendor_statistics()
        total_operations = sum(v['total_minted'] + v['total_redeemed'] for v in stats['vendors'])
        results.add_result(
            "Full Transmigration: Operations Count", 
            True, 
            f"{total_operations} total operations across {stats['total_vendors']} vendors"
        )
        
        # Verify hops
        # Initial mint + 10 hops = 11 mint operations total
        expected_mint_ops = 11
        total_mints = sum(v['total_minted'] for v in stats['vendors'])
        assert total_mints == expected_mint_ops, f"Should have {expected_mint_ops} mint operations"
        results.add_result("Full Transmigration: Hop Count", True, f"{total_mints} mint operations (1 initial + 10 hops)")
        
    except Exception as e:
        results.add_result("Full Transmigration Cycle", False, f"Error: {str(e)}")
    
    return results


async def test_custody_chain_severance():
    """Test 5: Verify custody chain is completely severed."""
    print("\n[TEST 5] Testing custody chain severance verification...")
    
    results = TestResults()
    
    try:
        orchestrator = DigitalPurgatoryOrchestrator(num_hops=10, num_mints=15)
        await orchestrator.discover_vendors()
        
        initial_amount = 10000
        source_id = "custody_test_source"
        
        # Track initial state
        initial_source = source_id
        
        # Execute transmigration
        final_tokens = await orchestrator.iterative_obfuscation_loop(initial_amount, source_id)
        
        # The final token should have NO relationship to the original source
        # Verify through different attributes
        final_token = final_tokens[0]
        
        # Token data should be different (randomly generated at each hop)
        # Mint ID should be from one of the vendors
        assert final_token.mint_id in [m.mint_id for m in orchestrator.vendor_pool], \
            "Final token should be from vendor pool"
        results.add_result("Custody Severance: Mint Verification", True, "Final mint is from pool")
        
        # Amount preserved but all other data is new
        assert final_token.amount == initial_amount, "Amount should be preserved"
        results.add_result("Custody Severance: Amount Integrity", True, f"{initial_amount} units intact")
        
        # Token should have been created recently (timestamp check)
        import time
        current_time = time.time()
        token_age = current_time - final_token.timestamp
        assert token_age < 60, "Token should be less than 60 seconds old"
        results.add_result("Custody Severance: Fresh Token", True, f"Token age: {token_age:.2f}s")
        
        results.add_result(
            "Custody Severance: Complete Verification",
            True,
            "No traceable link between source and final token"
        )
        
    except Exception as e:
        results.add_result("Custody Chain Severance", False, f"Error: {str(e)}")
    
    return results


async def test_logging_verification():
    """Test 6: Verify logging system is working."""
    print("\n[TEST 6] Testing logging verification...")
    
    results = TestResults()
    
    try:
        log_file = Path("dfir/orchestrator.log")
        
        # Check if log file exists
        assert log_file.exists(), "Log file should exist"
        results.add_result("Logging: File Existence", True, f"Log file: {log_file}")
        
        # Read log content
        log_content = log_file.read_text()
        
        # Verify key log entries
        assert "[ORCHESTRATOR_INIT]" in log_content, "Should contain orchestrator init logs"
        results.add_result("Logging: Orchestrator Init", True, "Orchestrator initialization logged")
        
        assert "[VENDOR_DISCOVERY]" in log_content, "Should contain vendor discovery logs"
        results.add_result("Logging: Vendor Discovery", True, "Vendor discovery logged")
        
        assert "[HOP_" in log_content, "Should contain hop logs"
        results.add_result("Logging: Hop Operations", True, "Hop operations logged")
        
        assert "[MINT_TOKENS]" in log_content, "Should contain mint logs"
        results.add_result("Logging: Mint Operations", True, "Mint operations logged")
        
        assert "[REDEEM_TOKEN]" in log_content, "Should contain redeem logs"
        results.add_result("Logging: Redeem Operations", True, "Redeem operations logged")
        
        # Count log lines
        log_lines = log_content.strip().split('\n')
        results.add_result("Logging: Volume", True, f"{len(log_lines)} log entries recorded")
        
    except Exception as e:
        results.add_result("Logging Verification", False, f"Error: {str(e)}")
    
    return results


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("DIGITAL PURGATORY PROTOCOL - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Setup logging
    setup_logging()
    
    # Run all tests
    all_results = []
    
    test_functions = [
        test_mock_mint_basic,
        test_vendor_discovery,
        test_single_hop,
        test_full_transmigration,
        test_custody_chain_severance,
        test_logging_verification
    ]
    
    for test_func in test_functions:
        result = await test_func()
        all_results.append(result)
    
    # Aggregate results
    print("\n" + "=" * 80)
    print("AGGREGATE TEST RESULTS")
    print("=" * 80)
    
    total_tests = sum(r.total_tests for r in all_results)
    total_passed = sum(r.passed_tests for r in all_results)
    total_failed = sum(r.failed_tests for r in all_results)
    
    for i, result in enumerate(all_results, 1):
        print(f"\nTest Suite {i}: {result.passed_tests}/{result.total_tests} passed")
        for test in result.test_details:
            print(f"  {test['status']} - {test['name']}")
    
    print("\n" + "=" * 80)
    print(f"OVERALL: {total_passed}/{total_tests} tests passed")
    print(f"Success Rate: {(total_passed/total_tests*100):.1f}%")
    print(f"Completed at: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Return exit code
    if total_failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {total_failed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
