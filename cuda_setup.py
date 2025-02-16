#!/usr/bin/env python3
"""
Script to detect CUDA version and install appropriate CUDA-enabled packages.
This is run after the main package is installed.
"""

import subprocess
import sys
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
        try:
            output = subprocess.check_output(["nvcc", "--version"]).decode()
            version = output.split("release ")[-1].split(",")[0]
            return version
        except:
            # Try nvidia-smi if nvcc fails
            output = subprocess.check_output(["nvidia-smi"]).decode()
            version = output.split("CUDA Version: ")[1].split(" ")[0]
            return version
    except Exception as e:
        logger.error(f"Failed to detect CUDA version: {str(e)}")
        return None

def install_cuda_packages():
    """Install CUDA-specific packages based on detected version."""
    cuda_version = get_cuda_version()
    if not cuda_version:
        logger.error("No CUDA installation found. GPU support will not be available.")
        return False

    try:
        cuda_major = cuda_version.split(".")[0]
        cuda_minor = cuda_version.split(".")[1]
        
        # Install CUDA-specific packages
        packages = [
            f"cupy-cuda{cuda_major}{cuda_minor}x>=12.0.0",
            "torch>=2.2.0+cu118",  # Latest PyTorch with CUDA support
            "torchvision>=0.17.0+cu118",
            "torchaudio>=2.2.0+cu118",
            "faiss-gpu>=1.7.2"
        ]
        
        for package in packages:
            logger.info(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info(f"Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {package}: {str(e)}")
                
        # Install PyTorch Geometric packages
        geometric_url = "https://data.pyg.org/whl/torch-2.2.0+cu118.html"
        geometric_packages = [
            "torch-scatter>=2.1.2",
            "torch-sparse>=0.6.18",
            "torch-cluster>=1.6.3",
            "torch-geometric>=2.4.0"
        ]
        
        for package in geometric_packages:
            logger.info(f"Installing {package}...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    package, "-f", geometric_url
                ])
                logger.info(f"Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {package}: {str(e)}")
        
        logger.info("\nNote: For RAPIDS libraries (cudf, cuspatial), please install via conda:")
        logger.info("conda install -c rapidsai -c conda-forge -c nvidia \\")
        logger.info(f"  cudf=24.2 cuspatial=24.2 python={sys.version_info.major}.{sys.version_info.minor} cuda-version={cuda_major}.{cuda_minor}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error installing CUDA packages: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" Installing CUDA-specific packages ")
    print("="*50 + "\n")
    
    success = install_cuda_packages()
    if success:
        print("\n✨ CUDA packages installation completed!")
    else:
        print("\n❌ CUDA packages installation failed. See logs for details.")
        sys.exit(1) 