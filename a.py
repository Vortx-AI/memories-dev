import faiss
import json
import os
from sentence_transformers import SentenceTransformer
import numpy as np

# Paths to FAISS index and metadata
FAISS_INDEX_PATH = "schema_index.faiss"          # Ensure this path is correct
METADATA_PATH = "schema_metadata.json"          # Ensure this path is correct

def load_faiss_index(index_path: str):
    """Load the FAISS index from file."""
    if not os.path.exists(index_path):
        print(f"FAISS index file '{index_path}' not found.")
        return None
    try:
        index = faiss.read_index(index_path)
        print(f"FAISS index loaded from '{index_path}'.")
        return index
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None

def load_metadata(metadata_path: str):
    """Load metadata information from a JSON file."""
    if not os.path.exists(metadata_path):
        print(f"Metadata file '{metadata_path}' not found.")
        return None
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print(f"Metadata loaded from '{metadata_path}'.")
        return metadata
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return None

def find_geometry_entries(metadata: list):
    """Find all entries related to the 'geometry' field."""
    geometry_entries = [entry for entry in metadata if entry.get('column_name', '').lower() == 'geometry']
    print(f"Found {len(geometry_entries)} entries for 'geometry' fields.")
    return geometry_entries

def display_geometry_entries(geometry_entries: list):
    """Display detailed information about each 'geometry' entry."""
    for entry in geometry_entries:
        print("\n--- Geometry Field Entry ---")
        print(f"Source: {entry.get('source')}")
        print(f"Table: {entry.get('table')}")
        print(f"File Path: {entry.get('file_path')}")
        print(f"Column Type: {entry.get('column_type')}")
        print(f"Record Count: {entry.get('record_count')}")
        if 'unique_values' in entry:
            print(f"Unique Values: {entry.get('unique_values')}")
        if 'null_count' in entry:
            print(f"Null Count: {entry.get('null_count')}")
        if 'samples' in entry:
            samples = entry.get('samples')
            print(f"Samples: {', '.join(map(str, samples[:3]))}")  # Display first 3 samples

def main():
    # Load FAISS index and metadata
    faiss_index = load_faiss_index(FAISS_INDEX_PATH)
    if faiss_index is None:
        return
    
    metadata = load_metadata(METADATA_PATH)
    if metadata is None:
        return
    
    # Find 'geometry' entries
    geometry_entries = find_geometry_entries(metadata)
    if not geometry_entries:
        print("No 'geometry' entries found in the metadata.")
        return
    
    # Display 'geometry' entries
    display_geometry_entries(geometry_entries)

if __name__ == "__main__":
    main()
