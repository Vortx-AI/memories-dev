.. mermaid::

    flowchart TD
        subgraph DataSources["Data Sources"]
            A1[Satellite Data]
            A2[Sensor Data]
            A3[Data Preprocessing]
        end

        subgraph Analysis["Analysis"]
            B1[Change Detection]
            B2[Trend Analysis]
            B3[Anomaly Detection]
        end

        subgraph Output["Output"]
            C1[Environmental Reports]
            C2[Risk Assessments]
            C3[Predictive Models]
        end

        A1 --> B1
        A2 --> B2
        A3 --> B3
        B1 --> C1
        B2 --> C2
        B3 --> C3

.. mermaid::

    flowchart TD
        subgraph ClimateData["Climate Data"]
            A1[Temperature]
            A2[Precipitation]
            A3[Wind Patterns]
            A4[Humidity]
        end

        subgraph AnalysisMethods["Analysis Methods"]
            B1[Statistical Analysis]
            B2[Machine Learning]
            B3[Physical Modeling]
        end

        subgraph Predictions["Predictions"]
            C1[Short-term Forecasts]
            C2[Long-term Projections]
            C3[Risk Scenarios]
        end

        A1 --> B1
        A2 --> B1
        A3 --> B2
        A4 --> B2
        B1 --> C1
        B2 --> C2
        B3 --> C3 