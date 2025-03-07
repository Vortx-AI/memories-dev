import pytest
import numpy as np
from memories.utils.earth.processors.comp import calculate_ndvi, transformer_process

def test_calculate_ndvi():
    """Test the NDVI calculation function."""
    # Test with simple data
    test_data = np.array([1, 2, 3])
    result = calculate_ndvi(test_data)
    assert np.array_equal(result, test_data), "NDVI calculation should return input data unchanged"

    # Test with empty array
    empty_data = np.array([])
    result = calculate_ndvi(empty_data)
    assert np.array_equal(result, empty_data), "NDVI calculation should handle empty arrays"

    # Test with None
    assert calculate_ndvi(None) is None, "NDVI calculation should handle None input"

def test_transformer_process():
    """Test the transformer process function."""
    # Test with simple data
    test_data = {"key": "value"}
    result = transformer_process(test_data)
    assert result == test_data, "Transformer should return input data unchanged"

    # Test with empty dict
    empty_data = {}
    result = transformer_process(empty_data)
    assert result == empty_data, "Transformer should handle empty dictionaries"

    # Test with None
    assert transformer_process(None) is None, "Transformer should handle None input" 