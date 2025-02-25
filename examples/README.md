# Examples

This directory contains example applications built using the Memories-Dev framework.

## What's New in Version 2.0.2 (Scheduled for February 25, 2025)

Since our initial release (v1.0.0 on February 14, 2025), we've added several new examples and improved existing ones:

### New Examples
- **Urban Planning Assistant**: Analyze urban areas for development planning
- **Environmental Monitoring**: Track changes in vegetation and land use over time
- **Location Context Analyzer**: Generate rich contextual descriptions of locations

### Improvements
- **Enhanced Visualization**: All examples now include improved visualization options
- **Performance Optimization**: Reduced memory usage and faster processing
- **Better Documentation**: More detailed comments and usage instructions

## Available Examples

### property_analyzer.py

A tool for analyzing property characteristics and surrounding areas.

**Setup:**
```bash
# Install required dependencies
pip install memories-dev[examples]

# Set up environment variables
export OPENSTREETMAP_API_KEY=your_api_key
export OVERTURE_API_KEY=your_api_key
```

**Usage:**
```python
from examples.property_analyzer import PropertyAnalyzer

# Initialize the analyzer
analyzer = PropertyAnalyzer()

# Analyze a property by address
results = analyzer.analyze_by_address("123 Main St, San Francisco, CA")

# Or analyze by coordinates
results = analyzer.analyze_by_coordinates(37.7749, -122.4194)

# Get the analysis report
print(results.summary)
print(results.nearby_amenities)
print(results.environmental_factors)
```

### water_bodies_monitor.py

A tool for monitoring water bodies and analyzing changes over time.

**Setup:**
```bash
# Install required dependencies
pip install memories-dev[examples]

# Set up environment variables
export OPENSTREETMAP_API_KEY=your_api_key
```

**Usage:**
```python
from examples.water_bodies_monitor import WaterBodiesMonitor
import asyncio

# Initialize the monitor
monitor = WaterBodiesMonitor(cache_dir="./water_bodies_cache")

# Define area of interest
bbox = {
    'xmin': -122.5,
    'ymin': 37.7,
    'xmax': -122.3,
    'ymax': 37.9
}

# Run the monitoring
async def monitor_water():
    # Get current water bodies
    water_bodies = await monitor.get_water_bodies(bbox)
    
    # Analyze changes over time
    changes = await monitor.analyze_changes(
        bbox,
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    
    return water_bodies, changes

# Run the async function
water_bodies, changes = asyncio.run(monitor_water())

# Print results
print(f"Found {len(water_bodies)} water bodies")
print(f"Detected {len(changes)} significant changes")
```

### location_ambience.py

A tool for generating rich descriptions of locations based on available data.

**Setup:**
```bash
# Install required dependencies
pip install memories-dev[examples]

# Set up environment variables
export OPENSTREETMAP_API_KEY=your_api_key
export DEEPSEEK_API_KEY=your_api_key  # Or use another supported model provider
```

**Usage:**
```python
from examples.location_ambience import LocationAmbience
import asyncio

# Initialize the ambience generator
ambience = LocationAmbience(
    model_provider="deepseek-ai",
    model_name="deepseek-coder-small"
)

# Define location
location = {
    'lat': 37.7749,
    'lon': -122.4194,
    'radius': 500  # meters
}

# Generate ambience description
async def generate_ambience():
    description = await ambience.generate_description(
        location,
        include_history=True,
        include_culture=True,
        include_architecture=True
    )
    return description

# Run the async function
description = asyncio.run(generate_ambience())

# Print the description
print(description)
```

### traffic_analyzer.py

A tool for analyzing traffic patterns and road network characteristics.

**Setup:**
```bash
# Install required dependencies
pip install memories-dev[examples]

# Set up environment variables
export OPENSTREETMAP_API_KEY=your_api_key
```

**Usage:**
```python
from examples.traffic_analyzer import TrafficAnalyzer
import asyncio

# Initialize the analyzer
analyzer = TrafficAnalyzer(cache_dir="./traffic_cache")

# Define area of interest
bbox = {
    'xmin': -122.5,
    'ymin': 37.7,
    'xmax': -122.3,
    'ymax': 37.9
}

# Analyze traffic
async def analyze_traffic():
    # Get road network
    road_network = await analyzer.get_road_network(bbox)
    
    # Analyze connectivity
    connectivity = await analyzer.analyze_connectivity(bbox)
    
    # Identify bottlenecks
    bottlenecks = await analyzer.identify_bottlenecks(bbox)
    
    return {
        'road_network': road_network,
        'connectivity': connectivity,
        'bottlenecks': bottlenecks
    }

# Run the async function
traffic_analysis = asyncio.run(analyze_traffic())

# Print results
print(f"Road network has {len(traffic_analysis['road_network'])} segments")
print(f"Connectivity score: {traffic_analysis['connectivity']['score']}")
print(f"Identified {len(traffic_analysis['bottlenecks'])} bottlenecks")
```

## Requirements

- Python 3.9+
- memories-dev framework (version 2.0.2)
- Environment variables for API access
- Additional dependencies specified in each example

## Common Usage Pattern

All examples follow a similar pattern:

1. Initialize the specific tool/analyzer
2. Define the area of interest (coordinates, bounding box, or address)
3. Call the appropriate methods to retrieve and analyze data
4. Process and visualize the results

## Data Storage

Each example stores its data in a configurable cache directory:

- `property_analyzer.py`: `./property_cache` (default)
- `water_bodies_monitor.py`: `./water_bodies_cache` (default)
- `location_ambience.py`: Uses in-memory cache only
- `traffic_analyzer.py`: `./traffic_cache` (default)

## Coming in Version 2.1.0 (March 2025)

- **Disaster Response Planning**: Analyze areas for natural disaster risks and plan response
- **Urban Heat Island Analysis**: Identify and analyze urban heat islands
- **Maxar Integration Examples**: Demonstrate high-resolution imagery analysis
- **Sentinel-3 Data Examples**: Show how to work with Sentinel-3 data

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