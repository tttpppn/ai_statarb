#!/usr/bin/env python3
"""
AI4Trade Signal Publisher
Publishes trading signals from the Ed Thorp strategy to the AI4Trade platform.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import requests

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import thorp_params

logger = logging.getLogger(__name__)


class AI4TradePublisher:
    """Publishes trading signals to AI4Trade platform."""

    def __init__(self):
        """Initialize publisher with API credentials."""
        self.api_url = thorp_params.AI4TRADE_API_URL
        self.api_token = thorp_params.AI4TRADE_API_TOKEN
        self.agent_id = thorp_params.AI4TRADE_AGENT_ID

        if not self.api_token:
            logger.warning("AI4TRADE_API_TOKEN not set - signal publishing disabled")

    def _get_headers(self) -> Dict:
        """Get request headers with authentication."""
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'User-Agent': f'ai4trade-statarb-agent/{self.agent_id}'
        }

    def publish_signal(self, signal: Dict) -> Optional[Dict]:
        """
        Publish a single trading signal to AI4Trade.

        Args:
            signal: {
                'symbol': 'TSMC',
                'action': 'long' or 'short',
                'entry_price': 125.50,
                'size': 500,
                'reasoning': 'Undervalued vs peers',
                'stop_loss': 120.0,
                'target': 135.0
            }

        Returns:
            Response from API or None if failed
        """
        if not self.api_token:
            logger.error("Cannot publish: API token not configured")
            return None

        try:
            payload = {
                'symbol': signal['symbol'],
                'action': signal['action'].lower(),
                'entry_price': float(signal['entry_price']),
                'quantity': int(signal.get('size', 100)),
                'reasoning': signal.get('reasoning', ''),
                'stop_loss': float(signal.get('stop_loss', 0)),
                'target': float(signal.get('target', 0)),
                'timestamp': datetime.now().isoformat(),
                'agent_id': self.agent_id
            }

            endpoint = f"{self.api_url}/signals/realtime"
            logger.info(f"Publishing signal: {signal['symbol']} {signal['action']} @ {signal['entry_price']}")

            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info(f"✓ Signal published: {signal['symbol']}")
                return response.json()
            elif response.status_code == 401:
                logger.error("✗ Authentication failed (401) - check API token")
                return None
            elif response.status_code == 429:
                logger.warning("Rate limited (429) - wait before next signal")
                return None
            else:
                logger.error(f"✗ Failed to publish: {response.status_code}")
                logger.error(f"  Response: {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"Error publishing signal: {e}")
            return None

    def publish_pair_signals(self, pair: Dict) -> bool:
        """
        Publish both sides of a trading pair (long + short).

        Args:
            pair: {
                'long_ticker': 'TSMC',
                'short_ticker': 'NVDA',
                'long_price': 125.50,
                'short_price': 875.00,
                'hedge_ratio': 1.2,
                'mispricing': 0.15
            }

        Returns:
            True if both signals published, False otherwise
        """
        long_signal = {
            'symbol': pair['long_ticker'],
            'action': 'long',
            'entry_price': pair['long_price'],
            'size': 100,
            'reasoning': f"Undervalued. Pair hedge: short {pair['short_ticker']} @ ratio {pair['hedge_ratio']:.2f}x",
            'stop_loss': pair['long_price'] * 0.95,
            'target': pair['long_price'] * 1.10
        }

        short_signal = {
            'symbol': pair['short_ticker'],
            'action': 'short',
            'entry_price': pair['short_price'],
            'size': int(100 * pair['hedge_ratio']),
            'reasoning': f"Overvalued. Pair hedge: long {pair['long_ticker']} @ ratio {1/pair['hedge_ratio']:.2f}x",
            'stop_loss': pair['short_price'] * 1.05,
            'target': pair['short_price'] * 0.90
        }

        result_long = self.publish_signal(long_signal)
        result_short = self.publish_signal(short_signal)

        return result_long is not None and result_short is not None

    def publish_screening_signals(self, screening_result: Dict) -> Dict:
        """
        Publish all signals from a daily screening.

        Args:
            screening_result: {
                'overvalued': [{'ticker': ..., 'score': ...}, ...],
                'undervalued': [{'ticker': ..., 'score': ...}, ...],
                'pairs': [...]
            }

        Returns:
            {
                'published': count,
                'failed': count,
                'pairs_published': count
            }
        """
        published = 0
        failed = 0
        pairs_published = 0

        # Publish pairs (more reliable than individual signals)
        if screening_result.get('pairs'):
            logger.info(f"Publishing {len(screening_result['pairs'])} pairs...")
            for pair in screening_result['pairs']:
                if self.publish_pair_signals(pair):
                    pairs_published += 1
                else:
                    failed += 1

            published = pairs_published * 2  # Each pair = 2 signals (long + short)

        return {
            'published': published,
            'failed': failed,
            'pairs_published': pairs_published,
            'timestamp': datetime.now().isoformat()
        }

    def get_agent_info(self) -> Optional[Dict]:
        """Fetch agent info from AI4Trade."""
        if not self.api_token:
            return None

        try:
            endpoint = f"{self.api_url}/claw/agents/me"
            response = requests.get(endpoint, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get agent info: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching agent info: {e}")
            return None

    def send_heartbeat(self) -> bool:
        """Send heartbeat to keep agent alive."""
        if not self.api_token:
            return False

        try:
            endpoint = f"{self.api_url}/claw/agents/heartbeat"
            payload = {
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'active'
            }

            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=5
            )

            if response.status_code in [200, 201]:
                logger.debug(f"✓ Heartbeat sent")
                return True
            else:
                logger.warning(f"Heartbeat failed: {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"Heartbeat error: {e}")
            return False


def test_publisher():
    """Test the publisher with mock data."""
    publisher = AI4TradePublisher()

    # Test agent info
    logger.info("=" * 80)
    logger.info("AI4TRADE PUBLISHER TEST")
    logger.info("=" * 80)

    agent_info = publisher.get_agent_info()
    if agent_info:
        logger.info(f"✓ Agent: {agent_info.get('name')} (ID: {agent_info.get('id')})")
        logger.info(f"  Cash: ${agent_info.get('cash', 0):,.0f}")
        logger.info(f"  Points: {agent_info.get('points', 0)}")
    else:
        logger.error("✗ Could not fetch agent info")

    # Test heartbeat
    if publisher.send_heartbeat():
        logger.info("✓ Heartbeat successful")
    else:
        logger.error("✗ Heartbeat failed")

    logger.info("=" * 80)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    test_publisher()
