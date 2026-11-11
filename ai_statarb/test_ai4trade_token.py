#!/usr/bin/env python3
"""
Test AI4Trade API Token
Tests connectivity and authentication with the AI4Trade platform.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import thorp_params

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_token():
    """Test AI4Trade token by making a simple API call."""

    token = os.getenv('AI4TRADE_API_TOKEN', '6hpFKg-fUqShgfeqNLb4LKgGV_TMZqtMk34GULg0yAo')
    api_url = os.getenv('AI4TRADE_API_URL', 'https://api.ai4trade.ai')
    agent_id = os.getenv('AI4TRADE_AGENT_ID', 'thorp-statarb-agent')

    logger.info("=" * 80)
    logger.info("AI4TRADE TOKEN TEST")
    logger.info("=" * 80)
    logger.info(f"API URL: {api_url}")
    logger.info(f"Agent ID: {agent_id}")
    logger.info(f"Token: {token[:20]}..." if token else "Token: NOT SET")
    logger.info("")

    if not token:
        logger.error("❌ FAILED: AI4TRADE_API_TOKEN is not set")
        logger.error("   Set it via: export AI4TRADE_API_TOKEN='your_token_here'")
        return False

    try:
        import requests
        logger.info("✓ requests library available")
    except ImportError:
        logger.error("❌ FAILED: requests library not installed")
        logger.error("   Install via: pip install requests")
        return False

    # Test 1: Verify token format
    logger.info("\n[TEST 1] Token format validation...")
    if len(token) < 20:
        logger.error(f"❌ FAILED: Token too short ({len(token)} chars)")
        return False
    logger.info(f"✓ Token length valid: {len(token)} chars")

    # Test 2: Test API connectivity
    logger.info("\n[TEST 2] API connectivity...")
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # AI4Trade specific endpoints
        test_endpoints = [
            f"{api_url}/claw/agents/me",
            f"{api_url}/api/claw/agents/me",
            f"{api_url}/claw/agents/heartbeat"
        ]

        response = None
        for endpoint in test_endpoints:
            try:
                logger.info(f"  Trying: {endpoint}")
                resp = requests.get(endpoint, headers=headers, timeout=5)
                if resp.status_code in [200, 401, 403]:  # Any real response is good
                    response = resp
                    break
            except requests.exceptions.RequestException as e:
                logger.debug(f"  {endpoint}: {e}")
                continue

        if response is None:
            logger.error("❌ FAILED: Could not reach any API endpoint")
            logger.error(f"   Tried: {test_endpoints}")
            return False

        logger.info(f"✓ API responded with status: {response.status_code}")

        if response.status_code == 401:
            logger.error("❌ FAILED: Token authentication failed (401 Unauthorized)")
            logger.error("   Token may be invalid or expired")
            return False

        if response.status_code == 403:
            logger.error("❌ FAILED: Token forbidden (403)")
            logger.error("   May need specific permissions")
            return False

        if response.status_code == 200:
            logger.info("✓ Authentication successful!")
            try:
                data = response.json()
                logger.info(f"✓ Response: {json.dumps(data, indent=2, default=str)[:200]}...")
            except:
                logger.info(f"✓ Response body: {response.text[:200]}...")

    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        return False

    # Test 3: Check config values
    logger.info("\n[TEST 3] Configuration check...")
    logger.info(f"  AI4TRADE_API_TOKEN (from env): {'SET' if os.getenv('AI4TRADE_API_TOKEN') else 'NOT SET'}")
    logger.info(f"  AI4TRADE_API_URL: {thorp_params.AI4TRADE_API_URL}")
    logger.info(f"  AI4TRADE_AGENT_ID: {thorp_params.AI4TRADE_AGENT_ID}")
    logger.info("✓ Configuration loaded")

    logger.info("\n" + "=" * 80)
    logger.info("✓ ALL TESTS PASSED - Token is valid and working!")
    logger.info("=" * 80)
    return True


if __name__ == '__main__':
    success = test_token()
    sys.exit(0 if success else 1)
