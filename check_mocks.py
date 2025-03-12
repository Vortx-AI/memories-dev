#!/usr/bin/env python
"""
Check if the diffusers module is properly mocked.

This script attempts to import diffusers and its submodules to verify
that they are properly mocked and will raise appropriate ImportError
exceptions when accessed.
"""

import os
import sys
import importlib
import traceback

def test_import(module_name):
    """Test importing a module and report the result."""
    print(f"Testing import of {module_name}...")
    try:
        module = importlib.import_module(module_name)
        print(f"  ✓ Successfully imported {module_name}")
        print(f"  Module type: {type(module)}")
        print(f"  Module path: {getattr(module, '__file__', 'No __file__ attribute')}")
        print(f"  Module attributes: {dir(module)[:5]}...")
        
        # Try accessing an attribute to see if it raises ImportError
        try:
            getattr(module, 'nonexistent_attribute')
            print(f"  ✗ ERROR: Accessing nonexistent attribute did not raise ImportError")
        except ImportError:
            print(f"  ✓ Accessing nonexistent attribute correctly raised ImportError")
        except Exception as e:
            print(f"  ✗ ERROR: Accessing nonexistent attribute raised {type(e).__name__} instead of ImportError")
            
        return True
    except ImportError as e:
        print(f"  ✓ ImportError raised as expected: {e}")
        return False
    except Exception as e:
        print(f"  ✗ ERROR: Unexpected exception: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

def main():
    """Main function to test diffusers mocking."""
    print("=" * 80)
    print("CHECKING DIFFUSERS MOCKING")
    print("=" * 80)
    
    # Check environment
    print("\nEnvironment:")
    print(f"Python version: {sys.version}")
    print(f"DISABLE_DIFFUSERS env var: {os.environ.get('DISABLE_DIFFUSERS', 'Not set')}")
    print(f"sys.path: {sys.path[:3]}...")
    
    # Test importing diffusers
    print("\nTesting diffusers imports:")
    modules_to_test = [
        'diffusers',
        'diffusers.loaders',
        'diffusers.loaders.single_file',
        'diffusers.pipelines',
        'diffusers.models',
    ]
    
    for module_name in modules_to_test:
        test_import(module_name)
        print()
    
    # Check if diffusers is in sys.modules
    print("\nChecking sys.modules:")
    for module_name in modules_to_test:
        if module_name in sys.modules:
            module = sys.modules[module_name]
            print(f"{module_name} is in sys.modules")
            print(f"  Type: {type(module)}")
            print(f"  File: {getattr(module, '__file__', 'No __file__ attribute')}")
        else:
            print(f"{module_name} is NOT in sys.modules")
    
    print("\nMock testing complete!")

if __name__ == "__main__":
    main() 