#!/usr/bin/env python3
import asyncio
import argparse
import sys
import json
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional

async def test_connection(host: str, port: int):
    """Test connection to the API server."""
    url = f"http://{host}:{port}/api/v1/memory/"
    print(f"Testing connection to {url}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Connection successful!")
                    print("\nAPI Information:")
                    print(f"Name: {data['name']}")
                    print(f"Version: {data['version']}")
                    print(f"Description: {data['description']}")
                    print("\nSupported Types:", ", ".join(data['supported_types']))
                    return True
                else:
                    print(f"❌ Connection failed with status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

async def process_query(host: str, port: int, query: str, api_key: str, 
                       message_type: str = "query", model_params: Optional[Dict] = None):
    """Process a query through the API."""
    url = f"http://{host}:{port}/api/v1/memory/process"
    
    request_data = {
        "text": query,
        "message_type": message_type,
        "api_key": api_key,
        "model_params": model_params or {}
    }
    
    print(f"\nSending query to {url}")
    print(f"Query: {query}")
    print(f"Type: {message_type}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=request_data) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("\nResponse received:")
                    print("================")
                    print(f"Status: {result['status']}")
                    print(f"Message: {result['message']}")
                    print(f"Timestamp: {result['timestamp']}")
                    print("\nData:")
                    print(json.dumps(result['data'], indent=2))
                    return True
                else:
                    print(f"\n❌ Query failed with status {response.status}")
                    print("Error:", result.get('detail', 'Unknown error'))
                    return False
                    
        except Exception as e:
            print(f"\n❌ Query failed: {e}")
            return False

async def run_basic_tests(host: str, port: int, api_key: str):
    """Run a series of basic tests."""
    tests = [
        ("What is the weather in New York?", "query"),
        ("Remember this important information.", "text"),
        ("execute analysis.py", "command")
    ]
    
    success = 0
    total = len(tests)
    
    for query, msg_type in tests:
        print(f"\nTesting {msg_type}: {query}")
        if await process_query(host, port, query, api_key, msg_type):
            success += 1
            
    print(f"\nTest Summary: {success}/{total} tests passed")

def main():
    parser = argparse.ArgumentParser(description='Test Memory Query API')
    parser.add_argument('--host', default='localhost', help='API server hostname or IP')
    parser.add_argument('--port', type=int, default=8000, help='API server port')
    parser.add_argument('--api-key', required=True, help='API key for authentication')
    parser.add_argument('--test', choices=['connection', 'query', 'basic'], 
                      default='connection', help='Type of test to run')
    parser.add_argument('--query', help='Query to test (when using --test query)')
    parser.add_argument('--type', choices=['text', 'query', 'command'],
                      default='query', help='Type of message to send')
    
    args = parser.parse_args()
    
    try:
        if args.test == 'connection':
            asyncio.run(test_connection(args.host, args.port))
        elif args.test == 'query':
            if not args.query:
                print("Error: --query parameter required for query test")
                sys.exit(1)
            asyncio.run(process_query(args.host, args.port, args.query, args.api_key, args.type))
        elif args.test == 'basic':
            asyncio.run(run_basic_tests(args.host, args.port, args.api_key))
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main() 