# Memories-Dev Examples

This directory contains example applications built using the Memories-Dev framework. Each example demonstrates different aspects of the framework's capabilities.

## What's New in Version 2.0.2

### New Examples
- **Urban Planning Assistant**: Analyze urban development using satellite imagery and vector data
- **Environmental Monitoring**: Track deforestation and environmental changes over time
- **Disaster Response Planning**: Create flood risk maps and evacuation plans
- **Multi-Provider Model Comparison**: Compare responses from different LLM providers

### Improvements
- **Enhanced Visualization**: Added interactive maps and charts using Folium and Matplotlib
- **Improved Data Integration**: Better integration with Overture Maps and OpenStreetMap
- **Multi-modal Processing**: Combined satellite imagery with vector data for richer analysis
- **Edge Deployment Examples**: Added examples for edge computing scenarios

## Available Examples

### 1. Property Analyzer (`property_analyzer.py`)
Analyzes real estate properties using satellite imagery and local context.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key

# Run the example
python property_analyzer.py
```

**New in 2.0.2**: Added property valuation using historical satellite imagery and neighborhood analysis.

### 2. Water Bodies Monitor (`water_bodies_monitor.py`)
Monitors and analyzes changes in global water bodies using satellite data.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key

# Run the example
python water_bodies_monitor.py
```

**New in 2.0.2**: Added drought prediction and water quality assessment using multi-spectral analysis.

### 3. Location Ambience (`location_ambience.py`)
Analyzes the ambience and environmental characteristics of locations.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key

# Run the example
python location_ambience.py
```

**New in 2.0.2**: Added noise level estimation and air quality prediction using environmental data.

### 4. Traffic Analyzer (`traffic_analyzer.py`)
Analyzes traffic patterns and road conditions using satellite imagery.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key

# Run the example
python traffic_analyzer.py
```

**New in 2.0.2**: Added congestion prediction and optimal route planning using historical traffic data.

### 5. Urban Planning Assistant (`urban_planning.py`) - NEW
Analyzes urban areas and provides planning recommendations.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key
export OPENAI_API_KEY=your_openai_api_key

# Run the example
python urban_planning.py
```

### 6. Environmental Monitoring (`environmental_monitoring.py`) - NEW
Tracks deforestation and environmental changes over time.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key
export ANTHROPIC_API_KEY=your_anthropic_api_key

# Run the example
python environmental_monitoring.py
```

### 7. Disaster Response Planning (`disaster_response.py`) - NEW
Creates flood risk maps and evacuation plans.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key
export OPENAI_API_KEY=your_openai_api_key

# Run the example
python disaster_response.py
```

### 8. Multi-Provider Model Comparison (`model_comparison.py`) - NEW
Compares responses from different LLM providers.

```bash
# Set up environment variables
export OPENAI_API_KEY=your_openai_api_key
export ANTHROPIC_API_KEY=your_anthropic_api_key
export DEEPSEEK_API_KEY=your_deepseek_api_key

# Run the example
python model_comparison.py
```

## Requirements

All examples require the following:

1. Python 3.9 or higher (updated in 2.0.2)
2. Memories-Dev framework v2.0.2 or higher
3. Required environment variables set (see each example's documentation)
4. Dependencies installed from `requirements.txt`

Install dependencies:
```bash
pip install -r requirements.txt
```

## Common Usage Pattern

All examples follow a similar pattern:

1. Initialize a memory store
2. Process data and generate insights
3. Store results in appropriate memory tiers

Example:
```python
from memories import MemoryStore, Config
from memories.data_acquisition.data_manager import DataManager
from memories.models.load_model import LoadModel
import asyncio

# Initialize components
config = Config(
    storage_path="./data",
    hot_memory_size=50,
    warm_memory_size=200,
    cold_memory_size=1000
)
memory_store = MemoryStore(config)
data_manager = DataManager(cache_dir="./data_cache")
model = LoadModel(
    model_provider="openai",
    deployment_type="api",
    model_name="gpt-4"
)

# Define area of interest
bbox = {
    'xmin': -122.4018,
    'ymin': 37.7914,
    'xmax': -122.3928,
    'ymax': 37.7994
}

# Process data
async def analyze_location():
    # Get satellite and vector data
    satellite_data = await data_manager.get_satellite_data(
        bbox_coords=bbox,
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
    
    vector_data = await data_manager.get_vector_data(
        bbox=bbox,
        layers=["buildings", "roads", "landuse"]
    )
    
    # Generate insights with LLM
    prompt = f"Analyze this location with the following data: {satellite_data}, {vector_data}"
    insights = model.get_response(prompt)
    
    # Store results
    memory_store.store(
        location=bbox,
        data_type="location_analysis",
        content=insights["text"]
    )
    
    return insights["text"]

# Run the analysis
results = asyncio.run(analyze_location())
print(results)

# Clean up
model.cleanup()
```

## Visualization Examples

### Interactive Maps with Folium (New in 2.0.2)

```python
import folium
from folium.plugins import HeatMap

# Create a map centered at the area of interest
m = folium.Map(
    location=[(bbox['ymin'] + bbox['ymax'])/2, (bbox['xmin'] + bbox['xmax'])/2],
    zoom_start=15
)

# Add buildings
for building in vector_data["buildings"][:1000]:  # Limit for performance
    folium.Polygon(
        locations=[[p[1], p[0]] for p in building.exterior.coords],
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.4
    ).add_to(m)

# Add a heatmap
heat_data = []
for point in data_points:
    heat_data.append([point.lat, point.lon, point.value])

HeatMap(heat_data).add_to(m)

# Save the map
m.save('analysis_map.html')
```

### Time Series Analysis with Matplotlib (New in 2.0.2)

```python
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

# Generate dates
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
dates = [start_date + timedelta(days=i) for i in range(0, 365, 30)]

# Generate values
values = [0.65 - (i * 0.02) for i in range(len(dates))]

# Create visualization
plt.figure(figsize=(12, 6))
plt.plot(dates, values, 'g-', marker='o')
plt.title('Environmental Change Over Time')
plt.xlabel('Date')
plt.ylabel('NDVI (Normalized Difference Vegetation Index)')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('environmental_trend.png')
```

## Data Storage

Each example stores its data in a different directory structure:
- Property Analyzer: `./property_data/`
- Water Bodies Monitor: `./water_bodies_data/`
- Location Ambience: `./location_data/`
- Traffic Analyzer: `./traffic_data/`
- Urban Planning: `./urban_planning_data/` (New in 2.0.2)
- Environmental Monitoring: `./environmental_data/` (New in 2.0.2)
- Disaster Response: `./disaster_response_data/` (New in 2.0.2)
- Model Comparison: `./model_comparison_data/` (New in 2.0.2)

## Edge Deployment Examples (New in 2.0.2)

For edge deployment scenarios with limited connectivity:

```python
from memories.deployments.standalone import StandaloneDeployment
from memories.models.load_model import LoadModel

# Configure edge deployment
edge_deployment = StandaloneDeployment(
    provider="local",
    config={
        "hardware": {
            "cpu": {"vcpus": 2},
            "memory": {"ram": 8},
            "storage": {"size": 50}
        },
        "network": {
            "offline_mode": True,
            "sync_interval": 3600  # Sync every hour when online
        }
    }
)

# Deploy the application
deployment_id = edge_deployment.deploy()

# Initialize local model for offline use
model = LoadModel(
    use_gpu=True,
    model_provider="deepseek-ai",
    deployment_type="local",
    model_name="deepseek-coder-small"
)

# Process data locally
response = model.get_response("Process this offline data")
print(response["text"])

# Clean up
model.cleanup()
```

## Contributing

Feel free to contribute your own examples! Follow these guidelines:
1. Create a new Python file in the examples directory
2. Add corresponding tests in `tests/examples/`
3. Update this README with information about your example
4. Ensure all tests pass before submitting a pull request

<p align="center">Built with 💜 by the memories-dev team</p> 