"""
Text processing utilities using NLTK.
"""

import nltk
import os
from typing import List, Tuple, NamedTuple, Dict, Any
from nltk.tokenize import PunktSentenceTokenizer, TreebankWordTokenizer, word_tokenize
from nltk.tag import pos_tag, RegexpTagger
from nltk.chunk import ne_chunk
from nltk.tree import Tree
import re

class Entity(NamedTuple):
    """Named entity with text and label."""
    text: str
    label: str

class TextProcessor:
    """Text processing utilities using NLTK."""
    
    def __init__(self):
        """Initialize the text processor."""
        # Define NLTK data paths
        nltk_data_paths = [
            os.path.expanduser('~/nltk_data'),  # User's home directory
            os.path.join(os.path.dirname(__file__), '..', 'data', 'nltk_data'),  # Package data directory
        ]
        
        # Add custom paths to NLTK's search path
        for path in nltk_data_paths:
            if path not in nltk.data.path:
                nltk.data.path.append(path)
        
        # Required NLTK resources and their types
        required_resources = [
            'punkt',
            'words'
        ]
        
        # Download and verify each resource
        for resource in required_resources:
            try:
                nltk.data.find(resource)
            except LookupError:
                try:
                    nltk.download(resource, quiet=True)
                except Exception as e:
                    raise RuntimeError(f"Failed to download NLTK resource {resource}: {str(e)}")
        
        # Initialize tokenizers
        self.word_tokenizer = TreebankWordTokenizer()
        self.sentence_tokenizer = PunktSentenceTokenizer()
        
        # Initialize a simple RegexpTagger as fallback
        patterns = [
            (r'.*ing$', 'VBG'),                # gerunds
            (r'.*ed$', 'VBD'),                 # simple past
            (r'.*es$', 'VBZ'),                 # 3rd singular present
            (r'.*ould$', 'MD'),                # modals
            (r'.*\'s$', 'NN$'),               # possessive nouns
            (r'.*s$', 'NNS'),                  # plural nouns
            (r'^-?[0-9]+(.[0-9]+)?$', 'CD'),  # cardinal numbers
            (r'.*', 'NN')                      # nouns (default)
        ]
        self.pos_tagger = RegexpTagger(patterns)

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        # First segment into sentences, then tokenize each sentence
        sentences = self.segment_sentences(text)
        tokens = []
        for sentence in sentences:
            tokens.extend(self.word_tokenizer.tokenize(sentence))
        return tokens

    def segment_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        return self.sentence_tokenizer.tokenize(text)

    def pos_tag(self, text: str) -> List[Tuple[str, str]]:
        """Tag parts of speech in the given text."""
        tokens = self.word_tokenizer.tokenize(text)
        return self.pos_tagger.tag(tokens)  # Use our own tagger instance

    def extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from the given text using simple rules."""
        tokens = self.word_tokenizer.tokenize(text)
        entities = []
        
        # Simple rule-based entity extraction
        i = 0
        while i < len(tokens):
            token = tokens[i]
            # Check for capitalized words that might be part of a multi-word entity
            if token[0].isupper() and i + 1 < len(tokens):
                # Look ahead for more capitalized words
                entity_tokens = [token]
                j = i + 1
                while j < len(tokens) and tokens[j][0].isupper():
                    entity_tokens.append(tokens[j])
                    j += 1
                if len(entity_tokens) > 1:
                    # Multi-word entity found
                    entity_text = ' '.join(entity_tokens)
                    entities.append(Entity(text=entity_text, label='GPE'))
                    i = j
                else:
                    # Single capitalized word
                    entities.append(Entity(text=token, label='GPE'))
                    i += 1
            else:
                i += 1
        
        return entities

    def preprocess(self, text: str) -> str:
        """Preprocess text for analysis."""
        # Convert to lowercase
        text = text.lower()
        # Tokenize
        tokens = self.tokenize(text)
        # Remove punctuation and join
        tokens = [token for token in tokens if token.isalnum()]
        return ' '.join(tokens)

    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Extract important keywords from text."""
        # Tokenize and pos tag
        pos_tags = self.pos_tag(text)
        
        # Keep only nouns and proper nouns
        keywords = [word.lower() for word, tag in pos_tags 
                   if tag.startswith(('NN', 'NNP'))]
        
        # Count frequencies
        from collections import Counter
        counts = Counter(keywords)
        
        # Return top N keywords with their frequencies
        total = sum(counts.values())
        return [(word, count/total) for word, count in counts.most_common(top_n)]

    def format_insights(self, insights: Dict[str, Any]) -> str:
        """Format insights into a readable string.
        
        Args:
            insights: Dictionary containing analysis insights
            
        Returns:
            Formatted string representation
        """
        lines = []
        for key, value in insights.items():
            if isinstance(value, dict):
                lines.append(f"{key.replace('_', ' ').title()}:")
                for subkey, subvalue in value.items():
                    if subvalue is not None:
                        lines.append(f"  - {subkey}: {subvalue:.2f}")
            elif value is not None:
                if isinstance(value, float):
                    lines.append(f"{key.replace('_', ' ').title()}: {value:.2f}")
                else:
                    lines.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(lines)
    
    def parse_location(self, location_str: str) -> List[float]:
        """Parse location string into coordinates.
        
        Args:
            location_str: String containing location information (e.g., "Bbox: [1.0, 2.0, 3.0, 4.0]")
            
        Returns:
            List of coordinates [min_x, min_y, max_x, max_y]
        """
        match = re.search(r"\[([\d\.\-\s,]+)\]", location_str)
        if match:
            coords = [float(x.strip()) for x in match.group(1).split(",")]
            return coords
        raise ValueError(f"Could not parse location string: {location_str}") 