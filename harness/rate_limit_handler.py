#!/usr/bin/env python3
"""
Rate Limit Handler for Parallel Harness

Manages Claude API rate limits with exponential backoff and adaptive throttling.

Phase 3: Auto-Claude Integration - Parallel Execution
"""

import time
import random
from typing import Optional
from datetime import datetime, timedelta


class RateLimitHandler:
    """
    Handles API rate limits with exponential backoff and adaptive throttling.

    Uses exponential backoff with jitter to handle transient rate limit errors.
    Tracks rate limit frequency to recommend reducing worker count if persistent.

    Example:
        handler = RateLimitHandler()

        # On rate limit error
        if error.status_code == 429:
            delay = handler.handle_error(error)
            time.sleep(delay)
            # Retry request

        # Check if should reduce workers
        if handler.should_reduce_workers():
            max_workers = max_workers // 2
    """

    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 10
    ):
        """
        Initialize rate limit handler.

        Args:
            initial_delay: Initial backoff delay in seconds (default: 1.0)
            max_delay: Maximum backoff delay in seconds (default: 60.0)
            max_retries: Maximum retry attempts before giving up (default: 10)
        """
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

        # Tracking
        self.rate_limit_count = 0
        self.consecutive_rate_limits = 0
        self.last_rate_limit_time = None
        self.rate_limit_history = []  # Track last 100 rate limits

    def get_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with jitter.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds to wait before retry
        """
        # Exponential backoff: initial_delay * (2 ** attempt)
        exponential_delay = self.initial_delay * (2 ** attempt)

        # Add jitter (random 0-1 seconds) to prevent thundering herd
        jitter = random.uniform(0, 1)

        # Cap at max_delay
        delay = min(exponential_delay + jitter, self.max_delay)

        return delay

    def should_retry(self, attempt: int) -> bool:
        """
        Check if should retry after rate limit error.

        Args:
            attempt: Current retry attempt number

        Returns:
            True if should retry, False if max retries exceeded
        """
        return attempt < self.max_retries

    def handle_error(self, error: Exception, attempt: int = 0) -> float:
        """
        Handle rate limit error and return delay before retry.

        Args:
            error: Exception that occurred (should be rate limit related)
            attempt: Current retry attempt number

        Returns:
            Delay in seconds to wait before retry

        Raises:
            Exception: If max retries exceeded, re-raises the error
        """
        # Track rate limit occurrence
        self.rate_limit_count += 1
        self.consecutive_rate_limits += 1
        self.last_rate_limit_time = datetime.now()

        # Add to history (keep last 100)
        self.rate_limit_history.append(datetime.now())
        if len(self.rate_limit_history) > 100:
            self.rate_limit_history.pop(0)

        # Check if should retry
        if not self.should_retry(attempt):
            print(f"⚠️  Max retries ({self.max_retries}) exceeded for rate limit")
            raise error

        # Calculate backoff delay
        delay = self.get_delay(attempt)

        print(f"⏳ Rate limit hit (attempt {attempt + 1}/{self.max_retries})")
        print(f"   Waiting {delay:.1f} seconds before retry...")

        return delay

    def reset_consecutive_count(self) -> None:
        """
        Reset consecutive rate limit counter.

        Call this after a successful request to track when rate limits
        are persistent vs transient.
        """
        self.consecutive_rate_limits = 0

    def should_reduce_workers(self, threshold: int = 3) -> bool:
        """
        Check if worker count should be reduced due to persistent rate limits.

        Args:
            threshold: Number of consecutive rate limits before recommending reduction

        Returns:
            True if should reduce workers, False otherwise
        """
        return self.consecutive_rate_limits >= threshold

    def get_rate_limit_rate(self, window_minutes: int = 5) -> float:
        """
        Calculate rate limit occurrence rate in recent time window.

        Args:
            window_minutes: Time window to analyze (default: 5 minutes)

        Returns:
            Rate limits per minute in the time window
        """
        if not self.rate_limit_history:
            return 0.0

        # Get rate limits in time window
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_rate_limits = [
            t for t in self.rate_limit_history if t >= cutoff_time
        ]

        # Calculate rate (rate limits per minute)
        if recent_rate_limits:
            return len(recent_rate_limits) / window_minutes
        else:
            return 0.0

    def get_stats(self) -> dict:
        """
        Get rate limit statistics.

        Returns:
            Dictionary with rate limit metrics
        """
        return {
            'total_rate_limits': self.rate_limit_count,
            'consecutive_rate_limits': self.consecutive_rate_limits,
            'rate_limit_rate_5min': self.get_rate_limit_rate(5),
            'last_rate_limit': self.last_rate_limit_time.isoformat() if self.last_rate_limit_time else None,
            'should_reduce_workers': self.should_reduce_workers()
        }

    def get_recommendation(self, current_workers: int) -> Optional[int]:
        """
        Get recommended worker count based on rate limit patterns.

        Args:
            current_workers: Current number of parallel workers

        Returns:
            Recommended worker count, or None if no change needed
        """
        if self.should_reduce_workers():
            # Reduce by half, but keep at least 1 worker
            recommended = max(current_workers // 2, 1)
            return recommended
        else:
            return None


# Utility function for simple rate limit handling
def handle_rate_limit_with_retry(
    func,
    max_retries: int = 5,
    initial_delay: float = 1.0
):
    """
    Decorator-style function to handle rate limits with retry.

    Args:
        func: Function to call
        max_retries: Maximum retry attempts
        initial_delay: Initial backoff delay

    Returns:
        Result of func() if successful

    Raises:
        Exception: If max retries exceeded

    Example:
        def call_api():
            # Code that might hit rate limits
            return client.messages.create(...)

        result = handle_rate_limit_with_retry(call_api, max_retries=5)
    """
    handler = RateLimitHandler(initial_delay=initial_delay, max_retries=max_retries)

    for attempt in range(max_retries):
        try:
            result = func()
            handler.reset_consecutive_count()
            return result

        except Exception as error:
            # Check if it's a rate limit error (429 status code)
            # This is a simplified check - real implementation would inspect error type
            error_str = str(error).lower()
            if '429' in error_str or 'rate limit' in error_str:
                delay = handler.handle_error(error, attempt)
                time.sleep(delay)
                continue
            else:
                # Not a rate limit error, re-raise
                raise

    # Max retries exceeded (shouldn't reach here due to handle_error raising)
    raise Exception(f"Max retries ({max_retries}) exceeded")


if __name__ == "__main__":
    # Example usage and testing
    print("Rate Limit Handler - Example")
    print()

    handler = RateLimitHandler(initial_delay=1.0, max_delay=60.0)

    print("Simulating rate limit backoff sequence:")
    print()

    for attempt in range(8):
        delay = handler.get_delay(attempt)
        print(f"Attempt {attempt + 1}: Wait {delay:.2f} seconds")

    print()
    print("Exponential backoff with jitter demonstrated:")
    print("  Attempt 1: ~1-2 seconds")
    print("  Attempt 2: ~2-3 seconds")
    print("  Attempt 3: ~4-5 seconds")
    print("  Attempt 4: ~8-9 seconds")
    print("  ...")
    print("  Attempt 7+: ~60-61 seconds (max delay)")
    print()

    # Simulate rate limit tracking
    print("Simulating rate limit tracking:")
    handler.rate_limit_count = 15
    handler.consecutive_rate_limits = 4

    stats = handler.get_stats()
    print(f"  Total rate limits: {stats['total_rate_limits']}")
    print(f"  Consecutive: {stats['consecutive_rate_limits']}")
    print(f"  Should reduce workers: {stats['should_reduce_workers']}")

    if stats['should_reduce_workers']:
        recommended = handler.get_recommendation(current_workers=6)
        print(f"  Recommendation: Reduce workers from 6 to {recommended}")
