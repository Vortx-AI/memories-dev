import os
import pytest
from pathlib import Path
from unittest.mock import patch
from sphinx.application import Sphinx
from sphinx.testing.util import SphinxTestApp

@pytest.fixture(autouse=True)
def mock_imports():
    """Mock problematic imports for testing."""
    with patch.dict('sys.modules', {
        'langchain': None,
        'langchain.llms.base': None,
        'langchain_core': None,
        'langchain_core.language_models': None,
        'langchain_core.messages': None,
        'langchain_core.utils': None,
    }):
        yield

@pytest.fixture
def sphinx_app():
    docs_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs')))
    build_dir = docs_dir / 'build'
    build_dir.mkdir(parents=True, exist_ok=True)
    
    app = SphinxTestApp(
        srcdir=docs_dir / 'source',
        confdir=docs_dir / 'source',
        outdir=build_dir,
        doctreedir=build_dir / 'doctrees',
        buildername='html',
        verbosity=0,
    )
    yield app
    app.cleanup()

def test_build_docs(sphinx_app):
    """Test that the documentation builds without errors."""
    app = sphinx_app
    app.build()
    assert app.statuscode == 0

def test_example_code_validity():
    """Test that code examples in documentation are valid Python."""
    import ast
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs'))
    examples_file = os.path.join(docs_dir, 'source', 'user_guide', 'examples.rst')
    
    with open(examples_file, 'r') as f:
        content = f.read()
    
    # Extract Python code blocks
    code_blocks = []
    current_block = []
    in_code_block = False
    
    for line in content.split('\n'):
        if line.strip() == '.. code-block:: python':
            in_code_block = True
            current_block = []
        elif in_code_block:
            if line.strip() and not line.startswith('    '):
                in_code_block = False
                if current_block:
                    code_blocks.append('\n'.join(current_block))
            else:
                # Remove the 4-space indentation from code blocks
                if line.startswith('    '):
                    line = line[4:]
                current_block.append(line)
    
    # Add the last block if we're still in one
    if current_block:
        code_blocks.append('\n'.join(current_block))
    
    # Validate each code block
    for code in code_blocks:
        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"Invalid Python code in documentation: {str(e)}\nCode block:\n{code}")

def test_version_consistency():
    """Test that version numbers are consistent across documentation."""
    import re
    
    # Read version from pyproject.toml
    with open('pyproject.toml', 'r') as f:
        content = f.read()
        version_match = re.search(r'version = "(.*?)"', content)
        assert version_match is not None, "Version not found in pyproject.toml"
        version = version_match.group(1)
    
    # Check version in conf.py
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs'))
    conf_py = os.path.join(docs_dir, 'source', 'conf.py')
    
    with open(conf_py, 'r') as f:
        conf_content = f.read()
    
    conf_version_match = re.search(r"version = '(.*?)'", conf_content)
    assert conf_version_match is not None, "Version not found in conf.py"
    assert conf_version_match.group(1) == version, f"Version mismatch: {conf_version_match.group(1)} != {version}"
    
    # Check version in __init__.py
    with open('memories/__init__.py', 'r') as f:
        init_content = f.read()
        init_version_match = re.search(r'__version__ = "(.*?)"', init_content)
        assert init_version_match is not None, "Version not found in __init__.py"
        assert init_version_match.group(1) == version, f"Version mismatch: {init_version_match.group(1)} != {version}"

def test_changelog_entries():
    """Test that changelog entries are properly formatted."""
    import re
    from datetime import datetime
    
    changelog_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CHANGELOG.md'))
    
    with open(changelog_file, 'r') as f:
        content = f.read()
    
    # Check version entry format
    version_pattern = r'## \[\d+\.\d+\.\d+\] - \d{4}-\d{2}-\d{2}'
    version_entries = re.findall(version_pattern, content)
    assert len(version_entries) > 0, "No valid version entries found in changelog"
    
    # Check date format and order
    dates = []
    for entry in version_entries:
        date_str = entry.split(' - ')[1]
        date = datetime.strptime(date_str, '%Y-%m-%d')
        dates.append(date)
    
    # Verify dates are in descending order
    assert dates == sorted(dates, reverse=True), "Changelog entries are not in descending order"

def test_api_reference_completeness():
    """Test that all public APIs are documented."""
    # Define the expected public APIs
    expected_apis = [
        'MemoryStore',
        'HotMemory',
        'WarmMemory',
        'ColdMemory',
        'GlacierMemory',
        'Config',
        'LoadModel',
        'gpu_stat',
        'query_multiple_parquet'
    ]
    
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs'))
    api_ref_dir = os.path.join(docs_dir, 'source', 'api_reference')
    
    # Get all RST files in the API reference directory
    rst_files = []
    for root, _, files in os.walk(api_ref_dir):
        rst_files.extend([os.path.join(root, f) for f in files if f.endswith('.rst')])
    
    # Read all RST files and check for API documentation
    all_content = ''
    for rst_file in rst_files:
        with open(rst_file, 'r') as f:
            all_content += f.read()
    
    # Check that each expected API is documented
    for api_name in expected_apis:
        assert api_name in all_content, f"API {api_name} is not documented" 