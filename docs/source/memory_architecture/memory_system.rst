Memory System Architecture
========================

.. mermaid::

    flowchart TD
        subgraph DataLayer["Data Layer"]
            A1[Satellite Imagery APIs]
            A2[Historical Maps]
            A3[GIS Data Sources]
            A4[Environmental Data]
            A5[Socioeconomic Data]
        end

        subgraph MemoryManagement["Memory Management Layer"]
            B1[Temporal Memory Manager]
            B2[Spatial Memory Manager]
            B3[Context Memory Manager]
            B4[Relationship Memory Manager]
        end

        subgraph ModelIntegration["Model Integration Layer"]
            C1[Computer Vision Models]
            C2[NLP Models]
            C3[Time Series Models]
            C4[Geospatial Models]
            C5[Multi-Modal Models]
        end

        subgraph ApplicationLayer["Application Layer"]
            D1[Real Estate Analysis]
            D2[Urban Planning]
            D3[Environmental Monitoring]
            D4[Historical Research]
            D5[Disaster Response]
        end

        A1 & A2 & A3 & A4 & A5 --> B1 & B2 & B3 & B4
        B1 & B2 & B3 & B4 --> C1 & C2 & C3 & C4 & C5
        C1 & C2 & C3 & C4 & C5 --> D1 & D2 & D3 & D4 & D5

        classDef acquisition fill:#3b82f6,color:#fff,stroke:#2563eb
        classDef memory fill:#10b981,color:#fff,stroke:#059669
        classDef model fill:#8b5cf6,color:#fff,stroke:#7c3aed
        classDef application fill:#f59e0b,color:#fff,stroke:#d97706

        class A1,A2,A3,A4,A5 acquisition
        class B1,B2,B3,B4 memory
        class C1,C2,C3,C4,C5 model
        class D1,D2,D3,D4,D5 application 