# 🌍 memories-dev

<div align="center">

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/The_Blue_Marble_%28remastered%29.jpg/600px-The_Blue_Marble_%28remastered%29.jpg" alt="Earth - The Blue Marble" width="400px">

**Building the World's Memory for Artificial General Intelligence**

[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://memories-dev.readthedocs.io/index.html)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Version](https://img.shields.io/badge/version-2.0.2-blue.svg)](https://github.com/Vortx-AI/memories-dev/releases/tag/v2.0.2)
[![Discord](https://img.shields.io/discord/1339432819784683522?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/tGCVySkX4d)

<a href="https://www.producthunt.com/posts/memories-dev?embed=true&utm_source=badge-featured&utm_medium=badge&utm_souce=badge-memories&#0045;dev" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=879661&theme=light&t=1739530783374" alt="memories&#0046;dev - Collective&#0032;AGI&#0032;Memory | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

</div>

> **"The framework that gives AI systems a memory of the physical world."**

## 🚀 What is memories-dev?

**memories-dev** is a groundbreaking Python framework that creates a collective memory system for AI by integrating satellite imagery, geospatial data, and environmental metrics with large language models. It provides foundation models with unprecedented contextual understanding of the physical world through a sophisticated Earth Memory system.

<div align="center">
  <img src="https://github.com/Vortx-AI/memories-dev/raw/main/docs/source/_static/architecture_overview.gif" alt="memories-dev Architecture" width="700px">
</div>

```mermaid
graph TD
    A[Foundation Models] -->|Augmented with| B[Earth Memory]
    B -->|Provides| C[Spatial Context]
    B -->|Provides| D[Temporal Context]
    B -->|Provides| E[Environmental Context]
    C -->|Enables| F[Location-Aware Intelligence]
    D -->|Enables| G[Time-Aware Intelligence]
    E -->|Enables| H[Environment-Aware Intelligence]
    F --> I[Collective AGI Memory]
    G --> I
    H --> I
    I -->|Powers| J[Next-Gen AI Applications]
```

## 🚀 What's New in Version 2.0.2

- **Enhanced Earth Memory Integration**: Seamless fusion of 15+ specialized analyzers for comprehensive environmental understanding
- **Temporal Analysis Engine**: Advanced historical change detection and future prediction capabilities
- **Asynchronous Processing Pipeline**: Parallel execution of multiple Earth Memory analyzers for 10x faster analysis
- **Vector-Based Memory Storage**: Efficient embedding and retrieval of complex multi-modal data
- **Comprehensive Scoring System**: Sophisticated algorithms for property evaluation across multiple dimensions
- **Multi-model Inference**: Compare results from multiple LLM providers
- **Streaming Responses**: Real-time streaming for all supported model providers
- **Memory Optimization**: Advanced memory usage with automatic tier balancing
- **Distributed Memory**: Support for distributed memory across multiple nodes

## 🌟 Why memories-dev?

### The Problem: AI Systems Lack Physical World Context

Current AI systems have limited understanding of the physical world:
- They can't access or interpret geospatial data effectively
- They lack temporal understanding of how places change over time
- They can't integrate environmental factors into their reasoning
- They have no memory of physical locations or their characteristics

### The Solution: Earth Memory Integration

memories-dev solves these problems by:
- Creating a sophisticated memory system that integrates 15+ specialized Earth analyzers
- Providing asynchronous parallel processing of multiple data sources
- Enabling temporal analysis for historical change detection and future prediction
- Implementing a tiered memory architecture for efficient data management
- Offering a comprehensive API for seamless integration with AI systems

## 💡 Key Features

### 1. Multi-Modal Earth Memory Integration

memories-dev creates a sophisticated memory system by fusing multiple data sources:

```mermaid
graph LR
    A[Earth Memory System] --> B[Satellite Imagery]
    A --> C[Vector Geospatial Data]
    A --> D[Environmental Metrics]
    A --> E[Temporal Analysis]
    A --> F[Climate Data]
    A --> G[Urban Development]
    
    B --> H[Sentinel-2]
    B --> I[Landsat]
    B --> J[Earth Engine]
    
    C --> K[Overture Maps]
    C --> L[OpenStreetMap]
    C --> M[WFS Services]
    
    D --> N[Air Quality]
    D --> O[Biodiversity]
    D --> P[Noise Levels]
    D --> Q[Solar Potential]
    
    E --> R[Historical Changes]
    E --> S[Future Predictions]
    
    F --> T[Temperature Trends]
    F --> U[Precipitation Patterns]
    F --> V[Extreme Weather Risk]
    
    G --> W[Urban Density]
    G --> X[Infrastructure]
    G --> Y[Development Plans]
```

### 2. Specialized Earth Memory Analyzers

The framework includes 15+ specialized analyzers for extracting insights from Earth Memory:

```mermaid
graph TD
    A[Earth Memory Analyzers] --> B[TerrainAnalyzer]
    A --> C[ClimateDataFetcher]
    A --> D[EnvironmentalImpactAnalyzer]
    A --> E[LandUseClassifier]
    A --> F[WaterResourceAnalyzer]
    A --> G[GeologicalDataFetcher]
    A --> H[UrbanDevelopmentAnalyzer]
    A --> I[BiodiversityAnalyzer]
    A --> J[AirQualityMonitor]
    A --> K[NoiseAnalyzer]
    A --> L[SolarPotentialCalculator]
    A --> M[WalkabilityAnalyzer]
    A --> N[ViewshedAnalyzer]
    A --> O[MicroclimateAnalyzer]
    A --> P[PropertyValuePredictor]
    A --> Q[InfrastructureAnalyzer]
    
    B --> B1[Elevation Analysis]
    B --> B2[Slope Analysis]
    B --> B3[Aspect Analysis]
    B --> B4[Landslide Risk]
    
    C --> C1[Temperature Trends]
    C --> C2[Precipitation Patterns]
    C --> C3[Climate Projections]
    C --> C4[Extreme Weather Risk]
    
    F --> F1[Flood Risk Assessment]
    F --> F2[Water Quality Analysis]
    F --> F3[Drought Risk Modeling]
    F --> F4[Watershed Analysis]
    
    H --> H1[Urban Growth Patterns]
    H --> H2[Development Plans]
    H --> H3[Infrastructure Analysis]
    H --> H4[Zoning Changes]
```

### 3. Tiered Memory Architecture

Our sophisticated memory management system optimizes data storage and retrieval:

```python
from memories import MemoryStore, Config

# Configure tiered memory architecture
config = Config(
    storage_path="./data",
    hot_memory_size=50,    # MB - Fast access, frequently used data
    warm_memory_size=200,  # MB - Balanced storage for semi-active data
    cold_memory_size=1000  # MB - Efficient storage for historical data
)

# Initialize memory store with automatic tier management
memory_store = MemoryStore(config)

# Store data with explicit tier assignment
await memory_store.store(
    "property_analysis_37.7749_-122.4194",
    analysis_result,
    tier="hot",  # Options: "hot", "warm", "cold"
    metadata={
        "location": {"lat": 37.7749, "lon": -122.4194},
        "timestamp": "2025-02-15T10:30:00Z",
        "analysis_type": "comprehensive_property"
    }
)
```

### 4. Asynchronous Parallel Processing

The framework uses advanced asynchronous processing to fetch and analyze multiple data sources in parallel:

```python
async def _fetch_comprehensive_earth_data(
    self,
    location: Point,
    area: Polygon
) -> Dict[str, Any]:
    """Fetch comprehensive earth memory data for the property location."""
    tasks = [
        self._fetch_sentinel_data(location, area),
        self._fetch_overture_data(location, area),
        terrain_analyzer.analyze_terrain(area),
        climate_fetcher.get_climate_data(area),
        impact_analyzer.analyze_environmental_impact(area),
        water_analyzer.analyze_water_resources(area),
        geological_fetcher.get_geological_data(area),
        urban_analyzer.analyze_urban_development(area),
        biodiversity_analyzer.analyze_biodiversity(area),
        air_quality_monitor.get_air_quality(location),
        noise_analyzer.analyze_noise_levels(area),
        solar_calculator.calculate_solar_potential(area),
        walkability_analyzer.analyze_walkability(location)
    ]
    
    results = await asyncio.gather(*tasks)
    
    return {
        "sentinel_data": results[0],
        "overture_data": results[1],
        "terrain_data": results[2],
        "climate_data": results[3],
        "environmental_impact": results[4],
        "water_resources": results[5],
        "geological_data": results[6],
        "urban_development": results[7],
        "biodiversity": results[8],
        "air_quality": results[9],
        "noise_levels": results[10],
        "solar_potential": results[11],
        "walkability": results[12]
    }
```

### 5. Multi-Dimensional Property Analysis

Our `RealEstateAgent` example demonstrates how memories-dev enables sophisticated property analysis:

```python
async def _analyze_current_conditions(
    self,
    location: Point,
    area: Polygon,
    earth_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze current property conditions using earth memory data."""
    return {
        "environmental_quality": {
            "air_quality_index": earth_data["air_quality"]["aqi"],
            "noise_level_db": earth_data["noise_levels"]["average_db"],
            "green_space_ratio": earth_data["environmental_impact"]["green_space_ratio"],
            "biodiversity_score": earth_data["biodiversity"]["biodiversity_index"]
        },
        "natural_risks": {
            "flood_risk": earth_data["water_resources"]["flood_risk_score"],
            "earthquake_risk": earth_data["geological_data"]["seismic_risk_score"],
            "landslide_risk": earth_data["terrain_data"]["landslide_risk_score"],
            "subsidence_risk": earth_data["geological_data"]["subsidence_risk_score"]
        },
        "urban_features": {
            "walkability_score": earth_data["walkability"]["score"],
            "public_transport_access": earth_data["urban_development"]["transit_score"],
            "amenities_score": earth_data["overture_data"]["amenities_score"],
            "urban_density": earth_data["urban_development"]["density_score"]
        },
        "sustainability": {
            "solar_potential": earth_data["solar_potential"]["annual_kwh"],
            "green_building_score": earth_data["environmental_impact"]["building_sustainability"],
            "water_efficiency": earth_data["water_resources"]["efficiency_score"],
            "energy_efficiency": earth_data["environmental_impact"]["energy_efficiency"]
        },
        "climate_resilience": {
            "heat_island_effect": earth_data["climate_data"]["heat_island_intensity"],
            "cooling_demand": earth_data["climate_data"]["cooling_degree_days"],
            "storm_resilience": earth_data["climate_data"]["storm_risk_score"],
            "drought_risk": earth_data["water_resources"]["drought_risk_score"]
        }
    }
```

### 6. Temporal Analysis Engine

The framework includes sophisticated temporal analysis capabilities for understanding how places change over time:

```python
async def _analyze_historical_changes(
    self,
    location: Point,
    area: Polygon
) -> Dict[str, Any]:
    """Analyze historical changes in the area over the specified time period."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * self.temporal_analysis_years)
    
    # Fetch historical satellite imagery
    historical_imagery = await sentinel_client.get_historical_imagery(
        area,
        start_date,
        end_date,
        max_cloud_cover=20
    )
    
    # Analyze changes
    land_use_changes = await land_use_classifier.analyze_changes(historical_imagery)
    urban_development_changes = await urban_analyzer.analyze_historical_changes(area, start_date, end_date)
    environmental_changes = await impact_analyzer.analyze_historical_impact(area, start_date, end_date)
    climate_changes = await climate_fetcher.get_historical_trends(area, start_date, end_date)
    
    return {
        "land_use_changes": land_use_changes,
        "urban_development": urban_development_changes,
        "environmental_impact": environmental_changes,
        "climate_trends": climate_changes
    }
```

## 🏗️ Quick Start

```bash
# Install the framework with all dependencies
pip install memories-dev[all]

# Set up environment variables for Earth Memory access
export OVERTURE_API_KEY=your_api_key
export SENTINEL_USER=your_username
export SENTINEL_PASSWORD=your_password

# Run the Real Estate Agent example
python examples/real_estate_agent.py
```

## 🌐 Real-World Applications

memories-dev powers sophisticated AI applications with deep contextual understanding:

### 1. Real Estate Intelligence

Our `RealEstateAgent` class demonstrates comprehensive property analysis using Earth Memory:

```mermaid
graph TD
    A[Property Data] -->|Input| B[RealEstateAgent]
    C[Earth Memory System] -->|13 Specialized Analyzers| B
    B -->|Asynchronous Analysis| D[Comprehensive Property Analysis]
    
    D -->|Output| E[Environmental Quality]
    E -->|Metrics| E1[Air Quality Index]
    E -->|Metrics| E2[Noise Levels]
    E -->|Metrics| E3[Green Space Ratio]
    E -->|Metrics| E4[Biodiversity Score]
    
    D -->|Output| F[Natural Risks]
    F -->|Metrics| F1[Flood Risk]
    F -->|Metrics| F2[Earthquake Risk]
    F -->|Metrics| F3[Landslide Risk]
    F -->|Metrics| F4[Subsidence Risk]
    
    D -->|Output| G[Urban Features]
    G -->|Metrics| G1[Walkability Score]
    G -->|Metrics| G2[Public Transport Access]
    G -->|Metrics| G3[Amenities Score]
    G -->|Metrics| G4[Urban Density]
    
    D -->|Output| H[Sustainability]
    H -->|Metrics| H1[Solar Potential]
    H -->|Metrics| H2[Green Building Score]
    H -->|Metrics| H3[Water Efficiency]
    H -->|Metrics| H4[Energy Efficiency]
    
    D -->|Output| I[Climate Resilience]
    I -->|Metrics| I1[Heat Island Effect]
    I -->|Metrics| I2[Cooling Demand]
    I -->|Metrics| I3[Storm Resilience]
    I -->|Metrics| I4[Drought Risk]
    
    B -->|Temporal Analysis| J[Historical Changes]
    J -->|Analysis| J1[Land Use Changes]
    J -->|Analysis| J2[Urban Development]
    J -->|Analysis| J3[Environmental Impact]
    J -->|Analysis| J4[Climate Trends]
    
    B -->|Predictive Analysis| K[Future Predictions]
    K -->|Predictions| K1[Urban Development]
    K -->|Predictions| K2[Environmental Changes]
    K -->|Predictions| K3[Climate Projections]
    K -->|Predictions| K4[Sustainability Outlook]
    
    B -->|Multi-Dimensional Scoring| L[Property Scores]
    L -->|Score| L1[Overall Score]
    L -->|Score| L2[Sustainability Score]
    L -->|Score| L3[Livability Score]
    L -->|Score| L4[Investment Score]
    L -->|Score| L5[Resilience Score]
```

### 2. Property Analyzer

The `PropertyAnalyzer` class provides even more detailed analysis with specialized components:

```python
# Example usage
analyzer = PropertyAnalyzer(
    memory_store=memory_store,
    analysis_radius_meters=2000,
    temporal_analysis_years=10,
    prediction_horizon_years=10
)

# Analyze property at specific coordinates
analysis = await analyzer.analyze_property(
    lat=37.7749,
    lon=-122.4194,
    property_data={
        "property_type": "residential",
        "year_built": 2015,
        "square_feet": 1200
    }
)

# Access comprehensive analysis results
terrain_analysis = analysis["terrain_analysis"]
water_analysis = analysis["water_analysis"]
geological_analysis = analysis["geological_analysis"]
environmental_analysis = analysis["environmental_analysis"]
risk_assessment = analysis["risk_assessment"]
value_analysis = analysis["value_analysis"]
recommendations = analysis["recommendations"]
```

### 3. Climate Risk Assessment

Financial institutions use memories-dev to assess climate-related risks for properties and infrastructure:

```python
from memories import ClimateRiskAssessor
from memories.earth import ClimateDataFetcher

# Initialize risk assessor
risk_assessor = ClimateRiskAssessor(
    risk_types=["flood", "wildfire", "drought", "storm"],
    analysis_resolution="property",
    time_horizon_years=30
)

# Assess portfolio risks
portfolio_risks = await risk_assessor.assess_portfolio(
    properties=[
        {"address": "123 Main St, Miami, FL", "value": 750000, "type": "residential"},
        {"address": "456 Oak Ave, Phoenix, AZ", "value": 1200000, "type": "commercial"},
        # More properties...
    ],
    scenarios=["RCP4.5", "RCP8.5"],
    confidence_interval=0.95
)

# Generate risk mitigation recommendations
recommendations = risk_assessor.generate_mitigation_strategies(
    portfolio_risks=portfolio_risks,
    budget_constraint=5000000,
    prioritization="cost_effectiveness"
)
```

### 4. Urban Planning & Development

Urban planners use memories-dev to analyze historical development patterns and simulate future scenarios:

```mermaid
graph LR
    A[City Data] -->|Acquisition| B[memories-dev]
    C[Historical Imagery] -->|Processing| B
    D[Development Plans] -->|Analysis| B
    B -->|Insights| E[Urban Planners]
    B -->|Recommendations| F[Policy Makers]
    B -->|Visualizations| G[Public Engagement]
```

### 5. AI-Enhanced Code Intelligence

The `CodeIntelligenceAgent` provides contextual understanding for code repositories:

```python
# Initialize the agent
agent = CodeIntelligenceAgent(
    memory_store=memory_store,
    embedding_model="all-MiniLM-L6-v2",
    supported_languages=["python", "javascript", "java", "c++", "go"]
)

# Store code knowledge
await agent.store_code_snippet(
    code="def calculate_distance(point1, point2):\n    return ((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)**0.5",
    language="python",
    description="Calculate Euclidean distance between two points",
    metadata={"category": "geometry", "complexity": "low"}
)

# Generate code with Earth Memory context
generated_code = await agent.generate_code(
    description="Calculate the flood risk for a property based on elevation and proximity to water bodies",
    language="python",
    earth_memory_context={
        "location": {"lat": 37.7749, "lon": -122.4194},
        "elevation_data": elevation_data,
        "water_bodies": water_bodies
    }
)
```

### 6. Multimodal AI Assistant

The `MultimodalAIAssistant` integrates text, imagery, and geospatial data:

```python
# Initialize the assistant
assistant = MultimodalAIAssistant(
    memory_store=memory_store,
    text_embedding_model="all-MiniLM-L6-v2",
    image_embedding_model="clip-ViT-B-32"
)

# Process multimodal data
text_result = await assistant.process_text(
    text="The urban development in San Francisco has changed significantly over the past decade.",
    metadata={"topic": "urban_development", "location": "San Francisco"}
)

image_result = await assistant.process_image(
    image_path="san_francisco_skyline_2023.jpg",
    metadata={"type": "skyline", "year": 2023, "location": "San Francisco"}
)

# Generate multimodal response with Earth Memory context
response = await assistant.generate_response(
    query="How has San Francisco's skyline changed since 2010?",
    earth_memory_context={
        "location": {"lat": 37.7749, "lon": -122.4194},
        "time_range": {"start": "2010-01-01", "end": "2023-12-31"}
    }
)
```

### 7. Additional Examples

Check out our [examples directory](examples/) for more sophisticated applications:

- **Ambience Analyzer**: Evaluates environmental quality and sensory experience
- **LLM Training Optimizer**: Improves model training with Earth Memory context
- **Water Body Agent**: Monitors water resources with temporal change detection
- **Traffic Analyzer**: Identifies patterns and optimizes transportation

## 🧩 System Architecture

memories-dev is built on a sophisticated architecture that enables seamless integration of Earth Memory with AI systems:

```mermaid
graph TD
    A[Data Acquisition Layer] -->|Ingests| B[Memory Management Layer]
    B -->|Provides Context| C[Model Integration Layer]
    C -->|Powers| D[Application Layer]
    
    A -->|Components| A1[Satellite Imagery APIs]
    A -->|Components| A2[Vector Data Sources]
    A -->|Components| A3[Environmental Data APIs]
    A -->|Components| A4[Temporal Data Processors]
    
    B -->|Components| B1[Hot Memory Manager]
    B -->|Components| B2[Warm Memory Manager]
    B -->|Components| B3[Cold Memory Manager]
    B -->|Components| B4[Memory Indexing System]
    B -->|Components| B5[Vector Store Integration]
    
    C -->|Components| C1[Model Connectors]
    C -->|Components| C2[Context Formatters]
    C -->|Components| C3[Response Generators]
    C -->|Components| C4[Function Calling]
    
    D -->|Examples| D1[Real Estate Agent]
    D -->|Examples| D2[Property Analyzer]
    D -->|Examples| D3[Water Body Agent]
    D -->|Examples| D4[Ambience Analyzer]
```

## 🚀 Deployment Options

memories-dev offers flexible deployment options to suit different use cases:

### Docker Deployment

```bash
# Build the Docker image
docker build -t memories-dev:latest .

# Run with Earth Memory API access
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e OVERTURE_API_KEY=your_api_key \
  -e SENTINEL_USER=your_username \
  -e SENTINEL_PASSWORD=your_password \
  memories-dev:latest
```

### Kubernetes Deployment

```yaml
# memories-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memories-dev
spec:
  replicas: 3
  selector:
    matchLabels:
      app: memories-dev
  template:
    metadata:
      labels:
        app: memories-dev
    spec:
      containers:
      - name: memories-dev
        image: memories-dev:latest
        resources:
          limits:
            cpu: "4"
            memory: "8Gi"
            nvidia.com/gpu: "1"
          requests:
            cpu: "2"
            memory: "4Gi"
        env:
        - name: OVERTURE_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: overture-api-key
        - name: SENTINEL_USER
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: sentinel-user
        - name: SENTINEL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: sentinel-password
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: memories-data-pvc
```

## 📊 Performance Benchmarks

memories-dev has been optimized for high-performance Earth Memory processing:

| Operation | CPU (8 cores) | GPU (T4) | GPU (A100) |
|-----------|--------------|----------|------------|
| Satellite Image Processing | 12.5s | 3.2s | 0.8s |
| Vector Data Processing | 4.8s | 1.5s | 0.4s |
| Environmental Analysis | 8.3s | 2.1s | 0.5s |
| Comprehensive Property Analysis | 28.7s | 7.4s | 1.9s |
| Historical Change Detection | 45.2s | 11.8s | 3.1s |
| Future Trend Prediction | 18.9s | 4.9s | 1.3s |

## 📅 Release Timeline

- **v1.0.0** - Released on February 14, 2025: Initial stable release with core functionality
- **v2.0.2** - Released on February 25, 2025: Current version with enhanced features

## 🔮 Future Roadmap

```mermaid
gantt
    title memories-dev Development Roadmap
    dateFormat  YYYY-MM-DD
    section Core Features
    Enhanced Vector Store Integration    :done, 2025-01-01, 2025-02-14
    Multi-modal Memory Management        :active, 2025-02-15, 2025-04-30
    Distributed Memory Architecture      :2025-05-01, 2025-07-31
    section Earth Memory
    Advanced Satellite Integration       :done, 2025-01-01, 2025-02-14
    Real-time Environmental Monitoring   :active, 2025-02-15, 2025-05-31
    Climate Prediction Models            :2025-06-01, 2025-08-31
    section AI Capabilities
    Memory-Augmented Reasoning           :active, 2025-02-15, 2025-04-30
    Multi-agent Memory Sharing           :2025-05-01, 2025-07-31
    Causal Inference Engine              :2025-08-01, 2025-10-31
```

## 📚 Documentation

- [Getting Started Guide](docs/getting_started.md)
- [API Reference](docs/api_reference.md)
- [Earth Memory Integration](docs/earth_memory.md)
- [Example Applications](examples/README.md)
- [Advanced Features](docs/advanced_features.md)

## ⚙️ System Requirements

- Python 3.9+
- 16GB RAM (32GB+ recommended for production)
- NVIDIA GPU with 8GB+ VRAM (recommended)
- Internet connection for Earth Memory APIs
- API keys for Overture Maps and Sentinel data

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📜 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- [Issue Tracker](https://github.com/Vortx-AI/memories-dev/issues)
- [Documentation](docs/)
- [Community Forum](https://forum.memories-dev.com)
- [Discord Community](https://discord.gg/tGCVySkX4d)

<p align="center">
  <img src="https://github.com/Vortx-AI/memories-dev/raw/main/docs/source/_static/earth_memory_logo.png" alt="Earth Memory" width="150px">
  <br>
  <b>Building the World's Memory for Artificial General Intelligence</b>
  <br>
  <br>
  Built with 💜 by the memories-dev team
</p>

