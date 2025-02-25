# Examples

This directory contains example applications built using the Memories-Dev framework.

## What's New in Version 2.0.2 (Scheduled for February 25, 2025)

Since our initial release (v1.0.0 on February 14, 2025), we've added several new examples and improved existing ones:

### New Examples
- **Real Estate Agent**: AI-powered property analysis with earth memory integration
- **Property Analyzer**: Comprehensive property and environmental analysis
- **Water Body Agent**: Advanced water body monitoring and analysis
- **Food Analyzer**: Intelligent food and nutrition analysis
- **Traffic Analyzer**: Real-time traffic pattern analysis
- **Autonomous Vehicle Memory**: Generalized car memory system with AI capabilities

### Improvements
- **Enhanced Earth Memory Integration**: All examples now include Overture and Sentinel data integration
- **Performance Optimization**: Reduced memory usage and faster processing
- **Better Documentation**: More detailed comments and usage instructions

## Available Examples

### real_estate_agent.py

An AI agent for analyzing real estate properties with earth memory integration.

**Setup:**
```bash
# Install required dependencies
pip install memories-dev[examples]

# Set up environment variables
export OVERTURE_API_KEY=your_api_key
export SENTINEL_USER=your_username
export SENTINEL_PASSWORD=your_password
```

**Usage:**
```python
from examples.real_estate_agent import RealEstateAgent
from memories import MemoryStore, Config

# Initialize memory store
config = Config(
    storage_path="./real_estate_data",
    hot_memory_size=50,
    warm_memory_size=200,
    cold_memory_size=1000
)
memory_store = MemoryStore(config)

# Initialize agent
agent = RealEstateAgent(memory_store, enable_earth_memory=True)

# Add a property
property_data = {
    "location": "San Francisco, CA",
    "coordinates": {"lat": 37.7749, "lon": -122.4194},
    "price": 1250000,
    "bedrooms": 2,
    "bathrooms": 2,
    "square_feet": 1200,
    "property_type": "Condo",
    "year_built": 2015
}

# Add property and analyze
result = await agent.add_property(property_data)
analysis = await agent.analyze_property_environment(result["property_id"])

print(f"Property added: {result['property_id']}")
print(f"Environmental analysis: {analysis}")
```

### property_analyzer.py

A tool for comprehensive property analysis using earth memory data.

**Setup:**
```bash
# Install required dependencies
pip install memories-dev[examples]

# Set up environment variables
export OVERTURE_API_KEY=your_api_key
export SENTINEL_USER=your_username
export SENTINEL_PASSWORD=your_password
```

**Usage:**
```python
from examples.property_analyzer import PropertyAnalyzer
from memories import MemoryStore, Config

# Initialize memory store
config = Config(
    storage_path="./property_analyzer_data",
    hot_memory_size=50,
    warm_memory_size=200,
    cold_memory_size=1000
)
memory_store = MemoryStore(config)

# Initialize analyzer
analyzer = PropertyAnalyzer(memory_store)

# Analyze property
analysis = await analyzer.analyze_property(
    lat=37.7749,
    lon=-122.4194,
    property_data={
        "address": "123 Main St, San Francisco, CA",
        "property_type": "residential"
    }
)

print("Analysis Results:")
print(f"Terrain Risks: {analysis['terrain_risks']}")
print(f"Water Resources: {analysis['water_resources']}")
print(f"Environmental Factors: {analysis['environmental_factors']}")
```

### water_body_agent.py

An AI agent for monitoring and analyzing water bodies.

**Setup:**
```bash
# Install required dependencies
pip install memories-dev[examples]

# Set up environment variables
export SENTINEL_USER=your_username
export SENTINEL_PASSWORD=your_password
```

**Usage:**
```python
from examples.water_body_agent import WaterBodyAgent
from memories import MemoryStore, Config

# Initialize memory store
config = Config(
    storage_path="./water_body_data",
    hot_memory_size=50,
    warm_memory_size=200,
    cold_memory_size=1000
)
memory_store = MemoryStore(config)

# Initialize agent
agent = WaterBodyAgent(memory_store)

# Analyze water body
analysis = await agent.analyze_water_body(
    coordinates={"lat": 37.7749, "lon": -122.4194},
    radius_meters=1000
)

print("Water Body Analysis:")
print(f"Water Quality: {analysis['water_quality']}")
print(f"Surface Area Changes: {analysis['surface_area_changes']}")
print(f"Environmental Impact: {analysis['environmental_impact']}")
```

## Requirements

- Python 3.9+
- memories-dev framework (version 2.0.2)
- Environment variables for API access
- Additional dependencies specified in each example

## Common Usage Pattern

All examples follow a similar pattern:

1. Initialize the memory store with appropriate configuration
2. Create an instance of the specific agent or analyzer
3. Provide necessary data or coordinates for analysis
4. Process the results and generate insights

## Data Storage

Each example stores its data in a configurable cache directory:

- `real_estate_agent.py`: `./real_estate_data` (default)
- `property_analyzer.py`: `./property_analyzer_data` (default)
- `water_body_agent.py`: `./water_body_data` (default)

## Coming in Version 2.1.0 (March 2025)

- **Food Analysis Agent**: Advanced food and nutrition analysis
- **Traffic Pattern Analyzer**: Real-time traffic monitoring and prediction
- **Autonomous Vehicle Memory**: Enhanced car memory system
- **Improved Earth Memory**: Additional data sources and analysis capabilities

## Contributing

We welcome contributions of new examples! To add your own example:

1. Create a new Python file in the `examples` directory
2. Follow the common pattern used in existing examples
3. Add comprehensive documentation and comments
4. Submit a pull request with your example

Please ensure your example includes:
- Clear setup instructions
- Usage examples
- Required dependencies
- Proper error handling
- Documentation comments

<p align="center">Built with 💜 by the memories-dev team</p> 