from datetime import datetime, timedelta
import os
import sys

# Add the parent directory to sys.path to make imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.rate_limiter_service import RateLimiterService

def test_rate_limiter():
    print("Testing Rate Limiter Logic...")
    
    max_requests = 2
    period_seconds = 7 * 24 * 3600
    
    # Simulate DB state
    current_count = 0
    last_reset = datetime.utcnow()
    
    # Request 1
    print("\n--- Request 1 ---")
    allowed, next_time, updates = RateLimiterService.check_rate_limit(current_count, last_reset, max_requests, period_seconds)
    print(f"Allowed: {allowed}")
    if allowed:
        current_count, last_reset = updates
        print(f"New Count: {current_count}")
    else:
        print("BLOCKED")

    # Request 2
    print("\n--- Request 2 ---")
    allowed, next_time, updates = RateLimiterService.check_rate_limit(current_count, last_reset, max_requests, period_seconds)
    print(f"Allowed: {allowed}")
    if allowed:
        current_count, last_reset = updates
        print(f"New Count: {current_count}")
    else:
        print("BLOCKED")
        
    # Request 3 (Should fail)
    print("\n--- Request 3 ---")
    allowed, next_time, updates = RateLimiterService.check_rate_limit(current_count, last_reset, max_requests, period_seconds)
    print(f"Allowed: {allowed}")
    if allowed:
        current_count, last_reset = updates
        print(f"New Count: {current_count}")
    else:
        print(f"BLOCKED as expected. Next available: {next_time}")

if __name__ == "__main__":
    test_rate_limiter()
