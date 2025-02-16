#!/usr/bin/env python3
"""
Script to install GPU-enabled dependencies for memories-dev.
This script will check your CUDA environment and install appropriate versions of PyTorch and related packages.
"""

import sys
import os
import subprocess
import logging
from typing import Optional, Tuple, List
import pkg_resources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_cuda_version() -> Optional[str]:
    """Get CUDA version from nvcc or nvidia-smi."""
    try:
        # Try nvcc first
        output = subprocess.check_output(["nvcc", "--version"]).decode()
        version = output.split("release ")[-1].split(",")[0]
        return version
    except Exception:
        try:
            # Try nvidia-smi if nvcc fails
            output = subprocess.check_output(["nvidia-smi"]).decode()
            version = output.split("CUDA Version: ")[1].split(" ")[0]
            return version
        except Exception:
            return None

def get_pytorch_commands(cuda_version: str) -> List[str]:
    """Get the appropriate pip install commands for PyTorch based on CUDA version."""
    cuda_major = cuda_version.split(".")[0]
    cuda_minor = cuda_version.split(".")[1]
    
    # Map CUDA versions to PyTorch CUDA versions
    cuda_map = {
        ("11", "8"): "cu118",
        ("12", "1"): "cu121",
        ("12", "2"): "cu122"
    }
    
    pytorch_cuda = cuda_map.get((cuda_major, cuda_minor), "cu118")  # Default to cu118 if version not found
    
    commands = []
    
    # Uninstall existing PyTorch packages
    commands.extend([
        "pip uninstall -y torch torchvision torchaudio",
        f"pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/{pytorch_cuda}"
    ])
    
    # PyTorch Geometric packages
    pyg_url = f"https://data.pyg.org/whl/torch-2.2.0+{pytorch_cuda}.html"
    commands.extend([
        f"pip install torch-scatter -f {pyg_url}",
        f"pip install torch-sparse -f {pyg_url}",
        f"pip install torch-cluster -f {pyg_url}",
        f"pip install torch-geometric -f {pyg_url}"
    ])
    
    # CUDA-specific packages
    commands.extend([
        f"pip install cupy-cuda{cuda_major}{cuda_minor}x>=12.0.0",
        "pip install faiss-gpu>=1.7.4"
    ])
    
    return commands

def install_gpu_dependencies():
    """Install GPU-enabled dependencies."""
    cuda_version = get_cuda_version()
    if not cuda_version:
        logger.error("❌ No CUDA installation found. Please install CUDA toolkit first.")
        sys.exit(1)
    
    logger.info(f"✅ Found CUDA version {cuda_version}")
    
    # Get installation commands
    commands = get_pytorch_commands(cuda_version)
    
    # Execute commands
    for cmd in commands:
        try:
            logger.info(f"\nExecuting: {cmd}")
            subprocess.check_call(cmd.split())
            logger.info("✅ Command completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Command failed: {str(e)}")
            if "faiss-gpu" in cmd and sys.version_info >= (3, 12):
                logger.warning("⚠️ Note: faiss-gpu is not available for Python 3.12+")
            else:
                logger.error("Please check your CUDA installation and try again.")
    
    # Print RAPIDS installation instructions
    logger.info("\nNote: For RAPIDS libraries (cudf, cuspatial), please install via conda:")
    logger.info("conda install -c rapidsai -c conda-forge -c nvidia \\")
    logger.info(f"  cudf=24.2 cuspatial=24.2 python={sys.version_info.major}.{sys.version_info.minor} cuda-version={cuda_version}")

def verify_installation():
    """Verify the GPU package installation."""
    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f"\n✅ PyTorch CUDA is available")
            logger.info(f"  - CUDA Version: {torch.version.cuda}")
            logger.info(f"  - PyTorch Version: {torch.__version__}")
            for i in range(torch.cuda.device_count()):
                logger.info(f"  - GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            logger.error("❌ PyTorch CUDA is not available")
    except ImportError:
        logger.error("❌ PyTorch is not installed")
    
    try:
        import torch_geometric
        logger.info(f"✅ PyTorch Geometric version: {torch_geometric.__version__}")
    except ImportError:
        logger.error("❌ PyTorch Geometric is not installed")

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" memories-dev GPU Dependencies Installer ")
    print("="*50 + "\n")
    
    install_gpu_dependencies()
    verify_installation()
    
    print("\n" + "="*50)
    print(" Installation Complete ")
    print("="*50 + "\n") 