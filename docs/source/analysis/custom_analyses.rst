================
Custom Analyses
================

Overview
--------

The memories-dev framework allows you to create custom analyses for specialized Earth observation tasks.

Creating Custom Analyzers
------------------------

Basic Structure
~~~~~~~~~~~~~~

.. code-block:: python

    from memories.analysis import BaseAnalyzer
    import numpy as np
    
    class CustomAnalyzer(BaseAnalyzer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.name = "custom_analyzer"
            
        async def analyze(self, data):
            """
            Implement custom analysis logic.
            
            Args:
                data: Input data to analyze
                
            Returns:
                dict: Analysis results
            """
            results = await self._process_data(data)
            return self._format_results(results)
            
        async def _process_data(self, data):
            # Implement processing logic
            pass
            
        def _format_results(self, results):
            # Format results for output
            pass

Example Implementation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class UrbanGrowthAnalyzer(BaseAnalyzer):
        def __init__(self, threshold=0.5, **kwargs):
            super().__init__(**kwargs)
            self.name = "urban_growth"
            self.threshold = threshold
            
        async def analyze(self, data):
            # Extract built-up area from multiple time points
            t1_built = await self._extract_built_area(data["t1"])
            t2_built = await self._extract_built_area(data["t2"])
            
            # Calculate growth metrics
            growth_rate = (t2_built - t1_built) / t1_built
            new_development = t2_built - t1_built
            
            return {
                "growth_rate": float(growth_rate),
                "new_development_area": float(new_development),
                "threshold_used": self.threshold
            }
            
        async def _extract_built_area(self, image):
            # Implement built-up area extraction
            built_mask = image > self.threshold
            return np.sum(built_mask)

Using Custom Analyzers
---------------------

.. code-block:: python

    from memories.data_acquisition import DataManager
    
    # Initialize components
    data_manager = DataManager()
    analyzer = UrbanGrowthAnalyzer(threshold=0.6)
    
    # Get data for analysis
    data = await data_manager.get_temporal_pair(
        bbox=bbox,
        t1="2020-01-01",
        t2="2024-01-01"
    )
    
    # Run analysis
    results = await analyzer.analyze(data)
    
    print(f"Urban growth rate: {results['growth_rate']:.2%}")
    print(f"New development: {results['new_development_area']:.2f} km²")

Validation and Testing
---------------------

.. code-block:: python

    from memories.testing import AnalyzerTester
    
    # Initialize tester
    tester = AnalyzerTester(analyzer)
    
    # Run validation tests
    validation_results = await tester.validate(
        test_data=test_dataset,
        metrics=["accuracy", "precision", "recall"]
    )
    
    # Print validation results
    print("Validation Results:")
    for metric, value in validation_results.items():
        print(f"{metric}: {value:.3f}")

Best Practices
-------------

1. **Documentation**
   - Clearly document input requirements
   - Explain analysis methodology
   - Provide usage examples

2. **Error Handling**
   - Validate input data
   - Handle edge cases
   - Provide informative error messages

3. **Performance**
   - Optimize computationally intensive operations
   - Use appropriate data structures
   - Implement caching where beneficial

4. **Testing**
   - Write unit tests
   - Include integration tests
   - Validate against known results

Integration
----------

.. code-block:: python

    from memories.pipeline import Pipeline
    
    # Create analysis pipeline
    pipeline = Pipeline()
    
    # Add custom analyzer
    pipeline.add_analyzer(
        analyzer=UrbanGrowthAnalyzer(),
        name="urban_growth",
        input_key="satellite_data",
        output_key="growth_metrics"
    )
    
    # Execute pipeline
    results = await pipeline.execute(input_data)

See Also
--------

* :doc:`/api_reference/analysis`
* :doc:`/integration/workflows`
* :doc:`/examples/custom_analysis` 