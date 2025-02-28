Application Layer Architecture
=========================

.. mermaid::

    flowchart TD
        A[Model Layer]
        B[Application Controller]
        C1[Visualization]
        C2[Reporting]
        C3[API Endpoints]
        C4[Decision Support]
        D[End Users]

        A --> B
        B --> C1
        B --> C2
        B --> C3
        B --> C4

        C1 & C2 & C3 & C4 --> D

        style A fill:#6d28d9,color:white
        style B fill:#9a3412,color:white
        style C1 fill:#9a3412,color:white
        style C2 fill:#9a3412,color:white
        style C3 fill:#9a3412,color:white
        style C4 fill:#9a3412,color:white
        style D fill:#1e40af,color:white 