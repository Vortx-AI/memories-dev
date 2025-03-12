#!/usr/bin/env python3
"""
Example script demonstrating the system check functionality.
"""

import memories
from memories.utils.core.system import system_check
from memories.config import configure_storage

def main():
    # Print version information
    print(f"\nMemories-dev version: {memories.__version__}")
    
    # Configure local storage (optional)
    configure_storage(
        storage_type="local",
        base_path="./data",
        cache_size_gb=10
    )
    
    # Run system check
    print("\nRunning system check...")
    status = system_check()
    
    # Print results
    print(f"\nSystem status: {'OK' if status.ok else 'Issues detected'}")
    
    if status.errors:
        print("\nErrors:")
        for error in status.errors:
            print(f"  {error}")
            
    if status.warnings:
        print("\nWarnings:")
        for warning in status.warnings:
            print(f"  {warning}")
            
    print("\nSystem messages:")
    for message in status.messages:
        print(f"  {message}")

if __name__ == "__main__":
    main() 