# Memories-Dev Examples

This directory contains example applications built using the Memories-Dev framework. Each example demonstrates different aspects of the framework's capabilities.

## Available Examples

### 1. Property Analyzer (`property_analyzer.py`)
Analyzes real estate properties using satellite imagery and local context.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key

# Run the example
python property_analyzer.py
```

### 2. Water Bodies Monitor (`water_bodies_monitor.py`)
Monitors and analyzes changes in global water bodies using satellite data.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key

# Run the example
python water_bodies_monitor.py
```

### 3. Location Ambience (`location_ambience.py`)
Analyzes the ambience and environmental characteristics of locations.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key

# Run the example
python location_ambience.py
```

### 4. Traffic Analyzer (`traffic_analyzer.py`)
Analyzes traffic patterns and road conditions using satellite imagery.

```bash
# Set up environment variables
export PLANETARY_COMPUTER_API_KEY=your_api_key

# Run the example
python traffic_analyzer.py
```

## Requirements

All examples require the following:

1. Python 3.8 or higher
2. Memories-Dev framework installed
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
from examples.property_analyzer import Property

# Initialize memory store
config = Config(
    storage_path="./data",
    hot_memory_size=50,
    warm_memory_size=200,
    cold_memory_size=1000
)
memory_store = MemoryStore(config)


property = Property(memory_store)

# Process data
insights = await property.analyze_property(property_data)
```

## Data Storage

Each example stores its data in a different directory structure:
- Property Analyzer: `./property_data/`
- Water Bodies Monitor: `./water_bodies_data/`
- Location Ambience: `./location_data/`
- Traffic Analyzer: `./traffic_data/`

## Contributing

Feel free to contribute your own examples! Follow these guidelines:
1. Create a new Python file in the examples directory
2. Add corresponding tests in `tests/examples/`
3. Update this README with information about your example
4. Ensure all tests pass before submitting a pull request 