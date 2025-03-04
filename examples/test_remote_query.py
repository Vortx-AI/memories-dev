#!/usr/bin/env python3
import asyncio
import argparse
import sys
import json
from memories.interface.webrtc import WebRTCClient

async def test_connection(host: str, port: int):
    """Test connection to the remote server."""
    print(f"Testing connection to {host}:{port}")
    client = WebRTCClient(host=host, port=port)
    try:
        print("Attempting to connect...")
        await client.connect()
        print("✅ Connection successful!")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    finally:
        if client:
            await client.close()

async def test_query(host: str, port: int, query: str):
    """Test a specific query."""
    client = WebRTCClient(host=host, port=port)
    try:
        print(f"Connecting to {host}:{port}")
        await client.connect()
        print("✅ Connection successful!")
        
        print(f"\nSending test query: {query}")
        result = await client.call_function("process_query", query)
        
        print("\nResponse received:")
        print("================")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Classification: {result.get('classification', 'unknown')}")
        print("\nResponse:")
        print(result.get('response', 'No response'))
        
        if 'results' in result:
            print("\nDetailed Results:")
            print(json.dumps(result['results'], indent=2))
            
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        if client:
            await client.close()

async def run_basic_tests(host: str, port: int):
    """Run a series of basic tests."""
    tests = [
        "What is the weather in New York?",
        "Find restaurants in San Francisco",
        "Tell me about the landmarks in Paris"
    ]
    
    success = 0
    total = len(tests)
    
    for query in tests:
        print(f"\nTesting query: {query}")
        if await test_query(host, port, query):
            success += 1
            
    print(f"\nTest Summary: {success}/{total} tests passed")

def main():
    parser = argparse.ArgumentParser(description='Test MemoryQuery WebRTC Server')
    parser.add_argument('--host', default='localhost', help='Server hostname or IP')
    parser.add_argument('--port', type=int, default=8765, help='Server port')
    parser.add_argument('--test', choices=['connection', 'query', 'basic'], 
                      default='connection', help='Type of test to run')
    parser.add_argument('--query', help='Query to test (when using --test query)')
    
    args = parser.parse_args()
    
    try:
        if args.test == 'connection':
            asyncio.run(test_connection(args.host, args.port))
        elif args.test == 'query':
            if not args.query:
                print("Error: --query parameter required for query test")
                sys.exit(1)
            asyncio.run(test_query(args.host, args.port, args.query))
        elif args.test == 'basic':
            asyncio.run(run_basic_tests(args.host, args.port))
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main() 