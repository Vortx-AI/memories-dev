# Installation Guide for memories-dev, pypi , git based.

## Prerequisites

### 1. Python Version
Ensure you have Python 3.9 or higher installed:
```bash
python --version  # Should be 3.9 or higher
```

### 2. Virtual Environment (Recommended)
Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv_memories

# Activate virtual environment
## On Windows:
venv_memories\Scripts\activate
## On macOS/Linux:
source venv_memories/bin/activate
```

### 3. System Dependencies

#### For Ubuntu/Debian:
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    python3-dev \
    gdal-bin \
    libgdal-dev \
    libspatialindex-dev \
    pandoc

# Set GDAL version
export GDAL_VERSION=$(gdal-config --version)
```

#### For macOS:
```bash
# Using Homebrew
brew update
brew install gdal
brew install spatialindex
brew install pandoc

# Set GDAL version
export GDAL_VERSION=$(gdal-config --version)
```

#### For Windows:
- Install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Install [GDAL](https://www.gisinternals.com/release.php)

## Installation Steps

### 1. Basic Installation

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install wheel and setuptools
pip install --upgrade wheel setuptools

# Install base package
pip install memories-dev
```

### 2. Install Additional Components

```bash
# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words')"

# Verify NLTK installation
python -c "import nltk; tokens = nltk.word_tokenize('Test'); print('NLTK installation successful!')"
```

### 3. GPU Support (Optional)
If you have a CUDA-capable GPU:

```bash
# Install GPU dependencies
pip install "memories-dev[gpu]"
```

### 4. Development Installation (Optional)
For development purposes:

```bash
# Clone the repository
git clone https://github.com/Vortx-AI/memories-dev.git
cd memories-dev

# Install in development mode with all extras
pip install -e ".[gpu,dev,docs]"
```

## Verification

Run the following test script to verify your installation:

```python
from memories.models.load_model import LoadModel
from memories.core.memory import MemoryStore

def test_installation():
    try:
        # Initialize model
        load_model = LoadModel(
            use_gpu=False,  # Set to True if using GPU
            model_provider="deepseek-ai",
            deployment_type="local",
            model_name="deepseek-r1-zero"
        )
        print("✅ Model initialization successful")

        # Initialize memory store
        memory_store = MemoryStore()
        print("✅ Memory store initialization successful")

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
        print("✅ Memory creation successful")
        print("\nInstallation verified successfully!")
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")

if __name__ == "__main__":
    test_installation()
```

Save this as `verify_install.py` and run:
```bash
python verify_install.py
```

## Troubleshooting

### Common Issues and Solutions

1. **GDAL Installation Issues**
   ```bash
   # If GDAL installation fails, try:
   pip install --no-binary :all: GDAL==${GDAL_VERSION}
   ```

2. **Torch Installation Issues**
   ```bash
   # If torch installation fails, try installing it separately first:
   pip install torch --index-url https://download.pytorch.org/whl/cpu  # For CPU
   # OR
   pip install torch --index-url https://download.pytorch.org/whl/cu118  # For CUDA 11.8
   ```

3. **Memory Issues During Installation**
   ```bash
   # If you encounter memory issues, try installing with pip's --no-cache option:
   pip install --no-cache-dir memories-dev
   ```

4. **Spatial Dependencies Issues**
   ```bash
   # If geopandas or rasterio fail, try:
   pip install wheel
   pip install pipwin
   pipwin install gdal
   pipwin install rasterio
   pipwin install geopandas
   ```

### Environment Variables

Set these environment variables if needed:
```bash
# For GDAL
export GDAL_LIBRARY_PATH=/usr/lib/libgdal.so  # Adjust path as needed
export GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so  # Adjust path as needed

# For memories-dev
export PROJECT_ROOT=/path/to/your/project  # Required for some features
```

## Support

If you encounter any issues:
1. Check our [GitHub Issues](https://github.com/Vortx-AI/memories-dev/issues)
2. Join our [Discord Community](https://discord.gg/7qAFEekp)
3. Email: hello@memories.dev 
