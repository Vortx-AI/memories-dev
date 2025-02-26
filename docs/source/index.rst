.. memories-dev documentation master file

======================
memories-dev Framework
======================

.. image:: https://img.shields.io/github/v/release/Vortx-AI/memories-dev?include_prereleases&style=flat-square
   :alt: GitHub release
   :target: https://github.com/Vortx-AI/memories-dev/releases

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square
   :alt: License
   :target: https://opensource.org/licenses/Apache-2.0

.. image:: https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square
   :alt: Python Versions
   :target: https://www.python.org/downloads/

.. image:: https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat-square
   :alt: Documentation
   :target: https://memories-dev.readthedocs.io/

.. raw:: html

   <div class="hero-banner">
     <div class="hero-image">
       <img src="_static/hero_image.png" alt="memories-dev Earth Memory System">
     </div>
     <div class="hero-content">
       <h1>Building Earth's Collective Memory System</h1>
       <p>A sophisticated framework for integrating geospatial data, historical imagery, and AI to create a comprehensive memory system for our planet.</p>
       <div class="hero-buttons">
         <a href="getting_started/installation.html" class="btn btn-primary">Get Started</a>
         <a href="https://github.com/Vortx-AI/memories-dev" class="btn btn-secondary">GitHub</a>
       </div>
     </div>
   </div>

   <style>
     .hero-banner {
       background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
       color: white;
       padding: 3rem 2rem;
       border-radius: 8px;
       margin: 2rem 0;
       box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
       display: flex;
       align-items: center;
       flex-wrap: wrap;
     }
     
     .hero-image {
       flex: 1;
       min-width: 300px;
       text-align: center;
       padding: 1rem;
     }
     
     .hero-image img {
       max-width: 100%;
       height: auto;
       border-radius: 8px;
       box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
     }
     
     .hero-content {
       flex: 2;
       min-width: 300px;
       padding: 1rem;
     }
     
     .hero-content h1 {
       font-size: 2.5rem;
       margin-bottom: 1rem;
       color: white;
       border-bottom: none;
     }
     
     .hero-content p {
       font-size: 1.2rem;
       margin-bottom: 2rem;
       opacity: 0.9;
     }
     
     .hero-buttons {
       display: flex;
       gap: 1rem;
       justify-content: center;
     }
     
     .btn {
       display: inline-block;
       padding: 0.75rem 1.5rem;
       border-radius: 4px;
       font-weight: 500;
       text-decoration: none;
       transition: all 0.2s ease-in-out;
     }
     
     .btn-primary {
       background-color: #3b82f6;
       color: white;
     }
     
     .btn-primary:hover {
       background-color: #2563eb;
       transform: translateY(-2px);
       box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
     }
     
     .btn-secondary {
       background-color: rgba(255, 255, 255, 0.1);
       color: white;
       border: 1px solid rgba(255, 255, 255, 0.2);
     }
     
     .btn-secondary:hover {
       background-color: rgba(255, 255, 255, 0.15);
       transform: translateY(-2px);
       box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
     }
     
     @media (max-width: 768px) {
       .hero-content h1 {
         font-size: 2rem;
       }
       
       .hero-content p {
         font-size: 1rem;
       }
       
       .hero-buttons {
         flex-direction: column;
         gap: 0.5rem;
       }
     }
   </style>

Preface
=======

Welcome to the comprehensive documentation for ``memories-dev``, Earth's Unified Memory System for Artificial General Intelligence. This documentation is designed to serve as a complete reference guide for developers, researchers, and organizations looking to implement or extend the memories-dev framework.

As the integration of AI with Earth observation data becomes increasingly important for applications in climate science, environmental monitoring, urban planning, and more, this framework provides the fundamental building blocks for creating AI systems that are grounded in observable physical reality.

This documentation is structured as a book, with chapters progressing from basic concepts to advanced implementation details. Whether you're a newcomer to the framework or an experienced developer, you'll find the information you need to harness the power of Earth's memory system.

.. raw:: html

   <div class="comparison-table">
     <h2>Beyond Traditional AI: Earth Memory vs. Foundation Models & RAG</h2>
     <div class="comparison-section">
       <h3>Traditional Foundation Models</h3>
       <ul class="negative-list">
         <li><span class="icon">❌</span> <strong>Limited to text corpora:</strong> Trained on internet text that may contain biases, inaccuracies, and outdated information</li>
         <li><span class="icon">❌</span> <strong>No direct observation:</strong> Cannot directly observe or verify physical world conditions</li>
         <li><span class="icon">❌</span> <strong>Static knowledge cutoff:</strong> Knowledge frozen at training time with no ability to access current conditions</li>
         <li><span class="icon">❌</span> <strong>Hallucination-prone:</strong> Prone to generating plausible but incorrect information about the physical world</li>
         <li><span class="icon">❌</span> <strong>No temporal understanding:</strong> Cannot track how places change over time</li>
       </ul>
     </div>
     
     <div class="comparison-section">
       <h3>Traditional RAG Systems</h3>
       <ul class="negative-list">
         <li><span class="icon">❌</span> <strong>Document-centric:</strong> Limited to retrieving text documents rather than rich multi-modal Earth data</li>
         <li><span class="icon">❌</span> <strong>Unstructured data:</strong> Typically works with unstructured text rather than structured geospatial information</li>
         <li><span class="icon">❌</span> <strong>Limited context window:</strong> Struggles with complex spatial and temporal relationships</li>
         <li><span class="icon">❌</span> <strong>No specialized analyzers:</strong> Lacks domain-specific tools for environmental and geospatial analysis</li>
         <li><span class="icon">❌</span> <strong>No multi-dimensional scoring:</strong> Cannot evaluate locations across multiple environmental dimensions</li>
       </ul>
     </div>
     
     <div class="comparison-section highlight-section">
       <h3>memories-dev Earth Memory System</h3>
       <ul class="positive-list">
         <li><span class="icon">✅</span> <strong>Direct observation:</strong> Integrates real satellite imagery and sensor data as ground truth</li>
         <li><span class="icon">✅</span> <strong>Multi-modal data fusion:</strong> Combines visual, vector, and environmental data for comprehensive understanding</li>
         <li><span class="icon">✅</span> <strong>Temporal awareness:</strong> Tracks changes over time with historical imagery and predictive capabilities</li>
         <li><span class="icon">✅</span> <strong>Specialized analyzers:</strong> 15+ domain-specific analyzers for terrain, climate, biodiversity, and more</li>
         <li><span class="icon">✅</span> <strong>Objective source of truth:</strong> Based on actual Earth observation data rather than potentially biased text</li>
         <li><span class="icon">✅</span> <strong>Spatial reasoning:</strong> Native understanding of geographic relationships and spatial context</li>
         <li><span class="icon">✅</span> <strong>Tiered memory architecture:</strong> Optimized storage and retrieval across hot, warm, cold, and glacier tiers</li>
         <li><span class="icon">✅</span> <strong>Asynchronous processing:</strong> 10x faster analysis through parallel execution of multiple Earth analyzers</li>
       </ul>
     </div>
   </div>

   <style>
     .comparison-table {
       margin: 2rem 0;
       padding: 1.5rem;
       background: #f8fafc;
       border-radius: 8px;
       box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
     }
     
     .comparison-table h2 {
       text-align: center;
       margin-bottom: 1.5rem;
       color: #0f172a;
       font-size: 1.8rem;
     }
     
     .comparison-section {
       margin-bottom: 2rem;
       padding: 1.5rem;
       border-radius: 8px;
       background: white;
       box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
     }
     
     .highlight-section {
       background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
       border-left: 4px solid #3b82f6;
     }
     
     .comparison-section h3 {
       margin-top: 0;
       margin-bottom: 1rem;
       color: #0f172a;
       font-size: 1.4rem;
     }
     
     .negative-list, .positive-list {
       list-style-type: none;
       padding-left: 0;
       margin-bottom: 0;
     }
     
     .negative-list li, .positive-list li {
       margin-bottom: 0.75rem;
       padding-left: 2rem;
       position: relative;
     }
     
     .icon {
       position: absolute;
       left: 0;
       top: 0.1rem;
       font-weight: bold;
     }
     
     .negative-list .icon {
       color: #ef4444;
     }
     
     .positive-list .icon {
       color: #10b981;
     }
     
     @media (max-width: 768px) {
       .comparison-table h2 {
         font-size: 1.5rem;
       }
     }
   </style>

Table of Contents
================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   
   getting_started/installation
   getting_started/quickstart
   getting_started/configuration
   getting_started/examples

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   
   user_guide/index
   user_guide/memory_system
   user_guide/data_sources
   user_guide/models
   user_guide/advanced_features
   user_guide/best_practices
   user_guide/configuration
   user_guide/deployment
   user_guide/examples

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts
   
   core_concepts/index
   core_concepts/architecture
   core_concepts/data_flow
   core_concepts/memory_system
   core_concepts/data_fusion

.. toctree::
   :maxdepth: 2
   :caption: Earth Memory
   
   earth_memory/index
   earth_memory/data_sources
   earth_memory/analyzers
   earth_memory/integration
   earth_memory/scientific_foundations

.. toctree::
   :maxdepth: 2
   :caption: Algorithms
   
   algorithms/index
   algorithms/kriging
   algorithms/point_pattern
   algorithms/time_series_decomposition

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   
   api_reference/index
   api_reference/data_utils
   api_reference/gpu_utils
   api_reference/load_model
   api_reference/memory_store
   api_reference/models
   api_reference/deployment
   api_reference/sentinel_api
   api_reference/utils

.. toctree::
   :maxdepth: 2
   :caption: Examples
   
   examples/index

.. toctree::
   :maxdepth: 2
   :caption: Metrics
   
   metrics/index
   metrics/environmental_metrics

.. toctree::
   :maxdepth: 2
   :caption: Documentation Guide
   
   matrix_theme_guide

Indices and Tables
=================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 