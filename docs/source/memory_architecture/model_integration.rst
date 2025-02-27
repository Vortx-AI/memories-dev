Model Integration Architecture
==========================

.. mermaid::

    flowchart TD
        A[Analysis Layer]
        B[Model Controller]
        C1[Computer Vision]
        C2[NLP Models]
        C3[Time Series Models]
        C4[Multi-Modal Models]
        D[Model Outputs]

        A --> B
        B --> C1
        B --> C2
        B --> C3
        B --> C4

        C1 & C2 & C3 & C4 --> D

        style A fill:#7c3aed,color:white
        style B fill:#6d28d9,color:white
        style C1 fill:#6d28d9,color:white
        style C2 fill:#6d28d9,color:white
        style C3 fill:#6d28d9,color:white
        style C4 fill:#6d28d9,color:white
        style D fill:#6d28d9,color:white 