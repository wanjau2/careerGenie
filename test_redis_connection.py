#!/usr/bin/env python3
"""Test Redis connection for CareerGenie."""

import redis
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_redis_connection():
    """Test Redis connection and basic operations."""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    print(f"Testing Redis connection to: {redis_url}")
    print("-" * 50)

    try:
        # Connect to Redis
        r = redis.from_url(redis_url)

        # Test 1: Ping
        print("Test 1: Ping Redis...")
        result = r.ping()
        print(f"✅ Redis responded: {result}")

        # Test 2: Set and Get
        print("\nTest 2: Set/Get operation...")
        test_key = 'careergenie_test_key'
        test_value = 'CareerGenie Redis Test'
        r.set(test_key, test_value)
        retrieved = r.get(test_key)
        print(f"✅ Set: '{test_value}'")
        print(f"✅ Got: '{retrieved.decode()}'")

        # Test 3: Expiration
        print("\nTest 3: Key expiration...")
        r.setex('temp_key', 5, 'temporary value')
        ttl = r.ttl('temp_key')
        print(f"✅ Set key with 5 second expiration, TTL: {ttl}s")

        # Test 4: Hash operations (used by Celery)
        print("\nTest 4: Hash operations...")
        r.hset('test_hash', 'field1', 'value1')
        r.hset('test_hash', 'field2', 'value2')
        hash_data = r.hgetall('test_hash')
        print(f"✅ Hash data: {hash_data}")

        # Test 5: List operations (used by Celery queue)
        print("\nTest 5: List operations...")
        r.lpush('test_list', 'item1', 'item2', 'item3')
        list_len = r.llen('test_list')
        print(f"✅ List length: {list_len}")

        # Test 6: Check Redis info
        print("\nTest 6: Redis server info...")
        info = r.info('server')
        print(f"✅ Redis version: {info['redis_version']}")
        print(f"✅ Redis mode: {info.get('redis_mode', 'standalone')}")
        print(f"✅ OS: {info['os']}")

        # Cleanup
        print("\nCleaning up test data...")
        r.delete(test_key, 'temp_key', 'test_hash', 'test_list')
        print("✅ Test data cleaned up")

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        return True

    except redis.ConnectionError as e:
        print(f"\n❌ Redis connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if Redis is running: redis-cli ping")
        print("2. Start Redis: sudo systemctl start redis")
        print("3. Check REDIS_URL in .env file")
        return False

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False


def test_celery_broker():
    """Test Celery broker connection."""
    celery_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

    print(f"\nTesting Celery broker connection to: {celery_url}")
    print("-" * 50)

    try:
        r = redis.from_url(celery_url)
        r.ping()
        print("✅ Celery broker (Redis) is reachable")

        # Check if any Celery tasks are in queue
        queue_length = r.llen('celery')
        print(f"✅ Celery queue length: {queue_length}")

        return True
    except Exception as e:
        print(f"❌ Celery broker test failed: {e}")
        return False


def test_rate_limiter():
    """Test rate limiter Redis connection."""
    ratelimit_url = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')

    print(f"\nTesting rate limiter connection to: {ratelimit_url}")
    print("-" * 50)

    try:
        r = redis.from_url(ratelimit_url)
        r.ping()
        print("✅ Rate limiter Redis is reachable")

        # Test rate limit key
        r.setex('test_ratelimit', 60, 1)
        print("✅ Rate limit test key created")
        r.delete('test_ratelimit')

        return True
    except Exception as e:
        print(f"❌ Rate limiter test failed: {e}")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("CAREERGENIE REDIS CONNECTION TEST")
    print("=" * 50)

    # Test main Redis connection
    test1 = test_redis_connection()

    # Test Celery broker
    test2 = test_celery_broker()

    # Test rate limiter
    test3 = test_rate_limiter()

    print("\n" + "=" * 50)
    print("FINAL RESULTS")
    print("=" * 50)
    print(f"Main Redis Connection:     {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Celery Broker Connection:  {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Rate Limiter Connection:   {'✅ PASS' if test3 else '❌ FAIL'}")
    print("=" * 50)

    # Exit with appropriate code
    sys.exit(0 if all([test1, test2, test3]) else 1)
