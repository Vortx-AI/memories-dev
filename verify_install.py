#!/usr/bin/env python3
"""
Verification script for memories-dev installation.
Run this script after installation to verify everything is working correctly.
"""

import sys
import os
import logging
import subprocess
from typing import Dict, List, Tuple, Optional
import pkg_resources
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_system_info() -> Dict[str, str]:
    """Get system information."""
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }
    
    # Check for CUDA
    try:
        output = subprocess.check_output(["nvidia-smi"]).decode()
        cuda_version = output.split("CUDA Version: ")[1].split(" ")[0]
        info["cuda_version"] = cuda_version
        
        # Get GPU info
        gpu_info = []
        for line in output.split("\n"):
            if "NVIDIA" in line and "%" in line:  # GPU line with usage info
                gpu_info.append(line.strip())
        info["gpu_info"] = gpu_info
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError) as e:
        logger.debug(f"CUDA detection failed: {e}")
        info["cuda_version"] = "Not found"
        info["gpu_info"] = []
    
    return info

def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    min_version = (3, 9)
    max_version = (3, 14)
    current_version = sys.version_info[:2]
    
    if min_version <= current_version < max_version:
        logger.info(f"✅ Python version {'.'.join(map(str, current_version))} meets requirements")
        return True
    else:
        logger.error(f"❌ Python version {'.'.join(map(str, current_version))} does not meet requirements")
        logger.error(f"   Required: >= {'.'.join(map(str, min_version))} and < {'.'.join(map(str, max_version))}")
        return False

def get_package_version(package: str) -> Optional[str]:
    """Get installed version of a package."""
    try:
        return pkg_resources.get_distribution(package).version
    except pkg_resources.DistributionNotFound:
        return None

def check_dependencies() -> Tuple[bool, List[str], List[str]]:
    """Check if all required dependencies are installed and working."""
    dependencies = {
        "Core ML/DL": [
            "torch",
            "transformers",
            "diffusers",
            "langchain",
            "langchain_community"
        ],
        "Data Processing": [
            "numpy",
            "pandas",
            "duckdb",
            "pyarrow"
        ],
        "GIS/Spatial": [
            "geopandas",
            "rasterio",
            "shapely",
            "mercantile",
            "mapbox_vector_tile",
            "pyproj",
            "pystac",
            "osmnx",
            "py6s",
            "geopy",
            "folium",
            "rtree"
        ],
        "Image Processing": [
            "pillow",
            "opencv-python",
            "albumentations"
        ],
        "AI/ML Tools": [
            "nltk",
            "faiss-cpu",
            "sentence_transformers"
        ],
        "Data Storage/Processing": [
            "redis",
            "xarray",
            "dask"
        ],
        "Web/API": [
            "fastapi",
            "pydantic",
            "uvicorn",
            "aiohttp",
            "requests"
        ],
        "Earth Observation": [
            "planetary_computer",
            "pystac_client",
            "earthengine-api"
        ],
        "Utilities": [
            "tqdm",
            "python-dotenv",
            "pyyaml",
            "cryptography",
            "typing_extensions",
            "fsspec",
            "noise"
        ]
    }
    
    installed = []
    missing = []
    version_conflicts = []
    
    logger.info("\nChecking dependencies:")
    for category, packages in dependencies.items():
        logger.info(f"\n{category}:")
        for package in packages:
            try:
                version = get_package_version(package.replace("-", "_"))
                if version:
                    installed.append(f"{package}=={version}")
                    logger.info(f"  ✅ {package} {version}")
                    
                    # Test import to catch runtime issues
                    try:
                        module_name = package.replace("-", "_")
                        __import__(module_name)
                    except ImportError as e:
                        logger.error(f"  ⚠️ {package} installed but import failed: {str(e)}")
                        version_conflicts.append(f"{package}: Import failed - {str(e)}")
                else:
                    missing.append(package)
                    logger.error(f"  ❌ {package} not found")
            except pkg_resources.VersionConflict as e:
                version_conflicts.append(f"{package}: {str(e)}")
                logger.error(f"  ⚠️ {package} version conflict: {str(e)}")
    
    if version_conflicts:
        logger.error("\nVersion conflicts found:")
        for conflict in version_conflicts:
            logger.error(f"  • {conflict}")
        logger.info("\nTo resolve conflicts:")
        logger.info("1. Create a new virtual environment")
        logger.info("2. Install dependencies in order:")
        logger.info("   pip install torch torchvision torchaudio")
        logger.info("   pip install -r requirements.txt")
        logger.info("   pip install memories-dev")
    
    return len(missing) == 0 and len(version_conflicts) == 0, installed, missing

def check_gpu_support() -> Tuple[bool, Dict[str, str]]:
    """Check GPU support and capabilities."""
    gpu_info = {}
    
    # Check CUDA availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["cuda_available"] = "Yes"
            gpu_info["cuda_version"] = torch.version.cuda
            gpu_info["torch_version"] = torch.__version__
            gpu_info["device_count"] = str(torch.cuda.device_count())
            
            devices = []
            for i in range(torch.cuda.device_count()):
                device = {
                    "name": torch.cuda.get_device_name(i),
                    "capability": f"{torch.cuda.get_device_capability(i)[0]}.{torch.cuda.get_device_capability(i)[1]}",
                    "memory": f"{torch.cuda.get_device_properties(i).total_memory / (1024**3):.1f} GB"
                }
                devices.append(device)
            gpu_info["devices"] = devices
            
            logger.info("\nGPU Support:")
            logger.info(f"  ✅ CUDA {gpu_info['cuda_version']} available")
            logger.info(f"  ✅ PyTorch {gpu_info['torch_version']} with CUDA support")
            for i, device in enumerate(devices):
                logger.info(f"  ✅ GPU {i}: {device['name']}")
                logger.info(f"     • Compute Capability: {device['capability']}")
                logger.info(f"     • Memory: {device['memory']}")
            
            return True, gpu_info
        else:
            gpu_info["cuda_available"] = "No"
            logger.warning("\n⚠️ CUDA is not available")
            return False, gpu_info
    except ImportError:
        gpu_info["cuda_available"] = "Error"
        logger.error("\n❌ Error checking CUDA support")
        return False, gpu_info

def check_pytorch_geometric() -> bool:
    """Check PyTorch Geometric installation."""
    try:
        import torch_geometric
        version = torch_geometric.__version__
        logger.info(f"\nPyTorch Geometric:")
        logger.info(f"  ✅ Version {version}")
        
        # Check CUDA support
        try:
            import torch_scatter
            import torch_sparse
            import torch_cluster
            logger.info("  ✅ CUDA extensions available")
            return True
        except ImportError:
            logger.warning("  ⚠️ CUDA extensions not found")
            return False
    except ImportError:
        logger.warning("  ⚠️ PyTorch Geometric not installed")
        return False

def test_basic_functionality() -> bool:
    """Test basic package functionality."""
    try:
        import memories
        logger.info(f"\nTesting memories-dev functionality:")
        logger.info(f"  ✅ Version {memories.__version__}")
        
        # Test core imports
        try:
            from memories.core.memory import MemoryStore
            from memories.models.load_model import LoadModel
            from memories.core.memories_index import HeaderMemory  # Added this import
            logger.info("  ✅ Core modules imported successfully")
            
            # Test geocoding functionality
            try:
                from geopy.geocoders import Nominatim
                geolocator = Nominatim(user="memories-dev-test")
                logger.info("  ✅ Geocoding functionality available")
            except Exception as e:
                logger.error(f"  ❌ Geocoding test failed: {str(e)}")
                return False
            
            return True
        except ImportError as e:
            logger.error(f"  ❌ Core module import failed: {str(e)}")
            logger.error("  💡 Try reinstalling the package: pip install -e .")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Error testing functionality: {str(e)}")
        if "No module named" in str(e):
            missing_module = str(e).split("'")[1]
            logger.error(f"  💡 Missing module: {missing_module}")
            logger.error(f"  💡 Install with: pip install {missing_module}")
        return False

def generate_report(
    system_info: Dict[str, str],
    dependencies_ok: bool,
    installed_packages: List[str],
    missing_packages: List[str],
    gpu_ok: bool,
    gpu_info: Dict[str, str],
    geometric_ok: bool,
    functionality_ok: bool
) -> str:
    """Generate installation report."""
    report = [
        "\n" + "="*50,
        " memories-dev Installation Report ",
        "="*50 + "\n",
        "System Information:",
        f"  OS: {system_info['os']} {system_info['os_version']}",
        f"  Python: {system_info['python_version']} ({system_info['python_implementation']})",
        f"  Machine: {system_info['machine']} ({system_info['processor']})",
        f"  CUDA: {system_info.get('cuda_version', 'Not found')}",
    ]
    
    if system_info.get('gpu_info'):
        report.extend([f"  GPU: {gpu}" for gpu in system_info['gpu_info']])
    
    report.extend([
        "\nInstallation Status:",
        f"  Dependencies: {'✅ Complete' if dependencies_ok else '❌ Incomplete'}",
        f"  GPU Support: {'✅ Available' if gpu_ok else '⚠️ Not available'}",
        f"  PyTorch Geometric: {'✅ Installed' if geometric_ok else '⚠️ Not installed'}",
        f"  Basic Functionality: {'✅ Working' if functionality_ok else '❌ Not working'}",
    ])
    
    if missing_packages:
        report.extend([
            "\nMissing Packages:",
            *[f"  • {pkg}" for pkg in missing_packages],
            "\nTo install missing packages:",
            "  pip install -r requirements.txt"
        ])
    
    if not gpu_ok and gpu_info.get('cuda_available') == 'No':
        report.extend([
            "\nGPU Support:",
            "  • CUDA is not available",
            "  • Run 'memories-gpu-setup' after installing CUDA toolkit"
        ])
    
    report.extend([
        "\nTroubleshooting Steps:",
        "1. If missing packages:",
        "   pip install -r requirements.txt",
        "",
        "2. If version conflicts:",
        "   a. Create new virtual environment:",
        "      python -m venv venv",
        "      source venv/bin/activate  # Linux/Mac",
        "      .\\venv\\Scripts\\activate  # Windows",
        "   b. Install dependencies in order:",
        "      pip install torch torchvision torchaudio",
        "      pip install -r requirements.txt",
        "      pip install memories-dev",
        "",
        "3. For GPU support:",
        "   memories-gpu-setup",
        "",
        "4. For development setup:",
        "   pip install -e .[dev]",
        "",
        "5. Documentation:",
        "   https://docs.memories.dev"
    ])
    
    return "\n".join(report)

def main():
    """Run all verification checks."""
    # Get system information
    system_info = get_system_info()
    
    # Check Python version
    python_ok = check_python_version()
    if not python_ok:
        logger.error("❌ Python version check failed. Please install a supported version.")
        sys.exit(1)
    
    # Check dependencies
    dependencies_ok, installed_packages, missing_packages = check_dependencies()
    
    # Check GPU support
    gpu_ok, gpu_info = check_gpu_support()
    
    # Check PyTorch Geometric
    geometric_ok = check_pytorch_geometric()
    
    # Test basic functionality
    functionality_ok = test_basic_functionality()
    
    # Generate and print report
    report = generate_report(
        system_info,
        dependencies_ok,
        installed_packages,
        missing_packages,
        gpu_ok,
        gpu_info,
        geometric_ok,
        functionality_ok
    )
    print(report)
    
    # Save report
    try:
        report_file = "memories_install_report.txt"
        with open(report_file, "w") as f:
            f.write(report)
        logger.info(f"\nReport saved to: {report_file}")
    except Exception as e:
        logger.error(f"Could not save report: {str(e)}")
    
    # Exit with appropriate status
    if not (dependencies_ok and functionality_ok):
        sys.exit(1)

if __name__ == "__main__":
    main() 