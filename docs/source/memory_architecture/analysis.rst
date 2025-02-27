Memory Analysis Framework
=======================

.. mermaid::

    flowchart TD
        A[Memory Layer]
        B[Analysis Controller]
        C1[Data Analysis]
        C2[Spatial Analysis]
        C3[Temporal Analysis]
        C4[Machine Learning]
        D[Analysis Results]

        A --> B
        B --> C1
        B --> C2
        B --> C3
        B --> C4

        C1 & C2 & C3 & C4 --> D

        style A fill:#047857,color:white
        style B fill:#7c3aed,color:white
        style C1 fill:#7c3aed,color:white
        style C2 fill:#7c3aed,color:white
        style C3 fill:#7c3aed,color:white
        style C4 fill:#7c3aed,color:white
        style D fill:#7c3aed,color:white 