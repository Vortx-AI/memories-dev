#!/usr/bin/env python3
"""
Verification script for memories-dev installation.
Run this script after installation to verify everything is working correctly.
"""

import sys
import os
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    required_version = (3, 9)
    current_version = sys.version_info[:2]
    
    if current_version >= required_version:
        logger.info(f"✅ Python version {'.'.join(map(str, current_version))} meets requirements")
        return True
    else:
        logger.error(f"❌ Python version {'.'.join(map(str, current_version))} does not meet minimum requirement of {'.'.join(map(str, required_version))}")
        return False

def check_dependencies() -> bool:
    """Check if all required dependencies are installed and working."""
    required_packages = [
        "torch",
        "transformers",
        "nltk",
        "numpy",
        "pandas",
        "geopandas",
        "rasterio",
        "duckdb",
        "faiss-cpu",
        "shapely"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is installed")
        except ImportError as e:
            logger.error(f"❌ {package} is not installed: {str(e)}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_nltk_data() -> bool:
    """Check if NLTK data is installed and working."""
    try:
        import nltk
        # Test NLTK components
        text = "Testing NLTK in San Francisco."
        tokens = nltk.word_tokenize(text)
        pos_tags = nltk.pos_tag(tokens)
        named_entities = nltk.ne_chunk(pos_tags)
        logger.info("✅ NLTK models are working")
        return True
    except Exception as e:
        logger.error(f"❌ NLTK model check failed: {str(e)}")
        return False

def check_gpu() -> bool:
    """Check if GPU is available and working."""
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"✅ GPU is available: {device_count} device(s)")
            logger.info(f"  - Device 0: {device_name}")
            return True
        else:
            logger.warning("⚠️ No GPU available, using CPU")
            return False
    except Exception as e:
        logger.error(f"❌ GPU check failed: {str(e)}")
        return False

def test_memory_creation() -> bool:
    """Test basic memory creation functionality."""
    try:
        from memories.models.load_model import LoadModel
        from memories.core.memory import MemoryStore
        
        # Initialize model
        load_model = LoadModel(
            use_gpu=False,  # Set to True if GPU check passed
            model_provider="deepseek-ai",
            deployment_type="local",
            model_name="deepseek-r1-zero"
        )
        logger.info("✅ Model initialization successful")
        
        # Initialize memory store
        memory_store = MemoryStore()
        logger.info("✅ Memory store initialization successful")
        
        # Test memory creation
        memories = memory_store.create_memories(
            model=load_model,
            location=(37.7749, -122.4194),
            time_range=("2024-01-01", "2024-02-01"),
            artifacts={
                "satellite": ["sentinel-2"],
                "landuse": ["osm"]
            }
        )
        logger.info("✅ Memory creation successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory creation test failed: {str(e)}")
        return False

def check_environment_variables() -> bool:
    """Check if required environment variables are set."""
    required_vars = ["PROJECT_ROOT"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            logger.error(f"❌ Environment variable {var} is not set")
    
    if not missing_vars:
        logger.info("✅ All required environment variables are set")
        return True
    return False

def main():
    """Run all verification checks."""
    logger.info("Starting memories-dev installation verification...")
    print("\n" + "="*50 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("GPU Availability", check_gpu),
        ("Environment Variables", check_environment_variables),
        ("Memory Creation", test_memory_creation)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        result = check_func()
        results.append((name, result))
        print("-"*50)
    
    print("\nVerification Summary:")
    print("="*50)
    all_passed = True
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✨ All checks passed! memories-dev is properly installed.")
    else:
        print("\n⚠️ Some checks failed. Please check the logs above and refer to INSTALL.md for troubleshooting.")

if __name__ == "__main__":
    main() 