"""
Phase 2 Integration Test
Tests AI Co-Pilot API endpoints and WebSocket connection
"""

import asyncio
import json
import requests
import time
from websockets import connect

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/copilot"


def test_copilot_status():
    """Test GET /api/copilot/status"""
    print("\n=== Test 1: Check Copilot Status ===")
    response = requests.get(f"{BASE_URL}/api/copilot/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_copilot_start():
    """Test POST /api/copilot/start"""
    print("\n=== Test 2: Start Copilot ===")
    response = requests.post(f"{BASE_URL}/api/copilot/start")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Check if we need to connect Muse first
    data = response.json()
    if data.get('status') == 'error' and 'not connected' in data.get('message', ''):
        print("\n⚠️  Muse not connected. Connect Muse first:")
        print("   1. Run: muselsl stream")
        print("   2. POST /api/connect")
        return False

    return response.status_code == 200


async def test_websocket_connection():
    """Test WebSocket /ws/copilot"""
    print("\n=== Test 3: WebSocket Connection ===")

    try:
        async with connect(WS_URL) as websocket:
            print("✅ WebSocket connected!")

            # Wait for initial greeting
            print("\nWaiting for messages (5 seconds)...")
            start_time = time.time()
            message_count = 0

            while time.time() - start_time < 5.0:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    message_count += 1

                    print(f"\n[Message {message_count}] Type: {data.get('type')}")
                    if data.get('type') == 'ai_message':
                        print(f"  AI: {data.get('text')}")
                    elif data.get('type') == 'transcript':
                        print(f"  Transcript: {data.get('text')}")
                    elif data.get('type') == 'state_update':
                        print(f"  Brain State: stress={data.get('brain_state', {}).get('stress', 'N/A')}")
                    elif data.get('type') == 'error':
                        print(f"  Error: {data.get('message')}")

                except asyncio.TimeoutError:
                    continue

            print(f"\n✅ Received {message_count} messages")
            return True

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False


def test_copilot_stop():
    """Test POST /api/copilot/stop"""
    print("\n=== Test 4: Stop Copilot ===")

    # Wait a bit for session to have some data
    print("Waiting 2 seconds...")
    time.sleep(2)

    response = requests.post(f"{BASE_URL}/api/copilot/stop")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_health_check():
    """Test basic server health"""
    print("\n=== Test 0: Server Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Server not running: {e}")
        print("\nPlease start the server:")
        print("  cd backend")
        print("  python3 main.py")
        return False


async def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Phase 2 Integration Test Suite")
    print("=" * 60)

    results = {}

    # Test 0: Health check
    results['health'] = test_health_check()
    if not results['health']:
        print("\n❌ Server not running. Aborting tests.")
        return results

    # Test 1: Status check
    results['status'] = test_copilot_status()

    # Test 2: Start copilot
    results['start'] = test_copilot_start()

    # Test 3: WebSocket (only if start succeeded)
    if results['start']:
        results['websocket'] = await test_websocket_connection()

        # Test 4: Stop copilot
        results['stop'] = test_copilot_stop()
    else:
        print("\n⚠️  Skipping WebSocket test (start failed)")
        results['websocket'] = False
        results['stop'] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")

    return results


if __name__ == "__main__":
    print("\n⚠️  PREREQUISITES:")
    print("1. Backend server running: python3 backend/main.py")
    print("2. (Optional) Muse connected: muselsl stream + POST /api/connect")
    print("3. OPENAI_API_KEY set in conversation_analyzer/.env.local")
    print("\nPress Enter to continue...")
    input()

    asyncio.run(run_all_tests())
