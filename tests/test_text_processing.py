import pytest
import nltk
from memories.utils.text import TextProcessor

@pytest.fixture(scope="session", autouse=True)
def download_nltk_data():
    """Download required NLTK data."""
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('maxent_ne_chunker_tab')
    nltk.download('words')

def test_text_processor_initialization():
    """Test that TextProcessor can be initialized."""
    processor = TextProcessor()
    assert processor is not None

def test_tokenization():
    """Test basic tokenization functionality."""
    processor = TextProcessor()
    text = "This is a test sentence about San Francisco."
    tokens = processor.tokenize(text)
    assert len(tokens) > 0
    assert "San" in tokens
    assert "Francisco" in tokens

def test_entity_recognition():
    """Test named entity recognition."""
    processor = TextProcessor()
    text = "San Francisco is located in California."
    entities = processor.extract_entities(text)
    assert any(entity.text == "San Francisco" for entity in entities)
    assert any(entity.text == "California" for entity in entities)

def test_sentence_segmentation():
    """Test sentence segmentation."""
    processor = TextProcessor()
    text = "First sentence. Second sentence. Third sentence."
    sentences = processor.segment_sentences(text)
    assert len(sentences) == 3

def test_pos_tagging():
    """Test part-of-speech tagging."""
    processor = TextProcessor()
    text = "The quick brown fox jumps over the lazy dog."
    pos_tags = processor.pos_tag(text)
    assert len(pos_tags) > 0
    assert all(isinstance(tag, tuple) and len(tag) == 2 for tag in pos_tags)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 