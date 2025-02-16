#!/usr/bin/env python3
"""
Script to install GPU-enabled dependencies for memories-dev.
This script will check your CUDA environment and install appropriate versions of PyTorch and related packages.
"""

import sys
import os
import subprocess
import logging
from typing import Optional, Tuple

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

def get_pytorch_command(cuda_version: str) -> Tuple[str, str]:
    """Get the appropriate pip install command for PyTorch based on CUDA version."""
    cuda_major = cuda_version.split(".")[0]
    cuda_minor = cuda_version.split(".")[1]
    
    # Map CUDA versions to PyTorch CUDA versions
    cuda_map = {
        ("11", "8"): "cu118",
        ("12", "1"): "cu121",
        ("12", "2"): "cu122"
    }
    
    pytorch_cuda = cuda_map.get((cuda_major, cuda_minor), "cu118")  # Default to cu118 if version not found
    
    base_command = f"pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/{pytorch_cuda}"
    geometric_command = f"pip install torch-scatter torch-sparse torch-cluster torch-geometric -f https://data.pyg.org/whl/torch-2.2.0+{pytorch_cuda}.html"
    
    return base_command, geometric_command

def install_gpu_dependencies():
    """Install GPU-enabled dependencies."""
    cuda_version = get_cuda_version()
    if not cuda_version:
        logger.error("❌ No CUDA installation found. Please install CUDA toolkit first.")
        sys.exit(1)
    
    logger.info(f"✅ Found CUDA version {cuda_version}")
    
    # Get appropriate install commands
    pytorch_command, geometric_command = get_pytorch_command(cuda_version)
    
    # Install dependencies
    try:
        logger.info("\nInstalling PyTorch with CUDA support...")
        subprocess.check_call(pytorch_command.split())
        
        logger.info("\nInstalling PyTorch Geometric...")
        subprocess.check_call(geometric_command.split())
        
        logger.info("\nInstalling other GPU dependencies...")
        gpu_deps = [
            "faiss-gpu>=1.7.4",
            f"cupy-cuda{cuda_version.replace('.', '')}x>=12.0.0",
            "cudf>=24.2.0",
            "cuspatial>=24.2.0"
        ]
        
        for dep in gpu_deps:
            try:
                subprocess.check_call(["pip", "install", dep])
            except subprocess.CalledProcessError:
                logger.warning(f"⚠️ Failed to install {dep} (optional)")
        
        logger.info("\n✨ GPU dependencies installation completed!")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error installing dependencies: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" memories-dev GPU Dependencies Installer ")
    print("="*50 + "\n")
    
    install_gpu_dependencies() 