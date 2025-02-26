.. mermaid::

    flowchart TD
        A[Memory Manager]
        B[Memory Controller]
        C1[Hot Memory]
        C2[Warm Memory]
        C3[Cold Memory]
        C4[Glacier Memory]

        B --> C1
        B --> C2
        B --> C3
        B --> C4

        C1 -.-> B
        C2 -.-> B
        C3 -.-> B
        C4 -.-> B

        classDef input fill:#3b82f6,color:#fff,stroke:#2563eb
        classDef manager fill:#8b5cf6,color:#fff,stroke:#7c3aed
        classDef hot fill:#ef4444,color:#fff,stroke:#dc2626
        classDef warm fill:#f59e0b,color:#fff,stroke:#d97706
        classDef cold fill:#10b981,color:#fff,stroke:#059669
        classDef glacier fill:#1e40af,color:#fff,stroke:#1e3a8a

        class A input
        class B manager
        class C1 hot
        class C2 warm
        class C3 cold
        class C4 glacier 