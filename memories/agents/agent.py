from typing import Dict, Any
from dotenv import load_dotenv
import logging
import os
from memories.agents.agent_query_classification import AgentQueryClassification
from memories.agents.agent_context import AgentContext
from memories.core.memory import MemoryStore

# Load environment variables
load_dotenv()

class Agent:
    def __init__(self, query: str, load_model: Any, memory_store: MemoryStore, instance_id: str = None):
        """
        Initialize the Agent system.
        
        Args:
            query (str): The user's query.
            load_model (Any): The initialized model instance.
            memory_store (MemoryStore): The memory store instance.
            instance_id (str, optional): The instance ID for FAISS search.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.query = query
        self.load_model = load_model
        self.memory_store = memory_store
        self.instance_id = instance_id
        
        # Retrieve PROJECT_ROOT from environment variables
        project_root = os.getenv("PROJECT_ROOT")
        if project_root is None:
            raise ValueError("PROJECT_ROOT environment variable is not set")

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query using the query classification agent and search FAISS if needed.
        
        Args:
            query (str): The user's query.
        
        Returns:
            Dict[str, Any]: The response containing the classification and result.
        """
        try:
            print("\n" + "="*50)
            print("QUERY PROCESSING PIPELINE")
            print("="*50)
            print(f"Input Query: {query}")
            print("="*50)
            
            # Step 1: Query Classification Agent
            print("\n1. Query Classification Agent")
            print("-"*30)
            classification_agent = AgentQueryClassification(query, self.load_model)
            classification_result = classification_agent.process_query()
            
            print(f"Classification: {classification_result.get('classification', '')}")
            print(f"Data Type: {classification_result.get('data_type', '')}")
            print(f"Explanation: {classification_result.get('explanation', '')}")
            
            result = classification_result
            data_type = result.get('data_type', '')
            
            # Step 2: FAISS Similarity Search
            if hasattr(self, 'instance_id') and data_type:
                print("\n2. FAISS Similarity Search")
                print("-"*30)
                print(f"Searching for data type: {data_type}")
                print(f"Instance ID: {self.instance_id}")
                
                try:
                    import faiss
                    import pickle
                    import os
                    import numpy as np
                    
                    project_root = os.getenv("PROJECT_ROOT")
                    faiss_dir = os.path.join(project_root, "data", "faiss")
                    
                    # Load FAISS index
                    index_path = os.path.join(faiss_dir, f"index_{self.instance_id}.faiss")
                    metadata_path = os.path.join(faiss_dir, f"metadata_{self.instance_id}.pkl")
                    
                    if os.path.exists(index_path) and os.path.exists(metadata_path):
                        self.faiss_index = faiss.read_index(index_path)
                        with open(metadata_path, 'rb') as f:
                            self.faiss_metadata = pickle.load(f)
                        print(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")
                        
                        # Create a random query vector (replace with proper embedding in production)
                        query_vector = np.random.rand(1, self.faiss_index.d).astype('float32')
                        
                        # Search similar vectors
                        k = 5  # number of nearest neighbors
                        distances, indices = self.faiss_index.search(query_vector, k)
                        
                        # Get metadata for similar columns
                        similar_columns = []
                        for idx, (distance, index) in enumerate(zip(distances[0], indices[0])):
                            if index < len(self.faiss_metadata):
                                metadata = self.faiss_metadata[index]
                                similarity_score = float(1.0 / (1.0 + distance))
                                similar_columns.append({
                                    'column_name': metadata['column_name'],
                                    'file_path': metadata['file_path'],
                                    'file_name': metadata['file_name'],
                                    'similarity_score': similarity_score,
                                    'data_type': data_type,
                                    'vector_id': metadata.get('vector_id', index)
                                })
                        
                        print("\nSimilar columns found:")
                        for col in similar_columns:
                            print(f"\nColumn: {col['column_name']}")
                            print(f"File: {col['file_name']}")
                            print(f"Score: {col['similarity_score']:.3f}")
                            print(f"Vector ID: {col['vector_id']}")
                        
                        result['similar_columns'] = similar_columns
                        result['vector_search'] = {
                            'query_type': data_type,
                            'total_vectors': self.faiss_index.ntotal,
                            'dimension': self.faiss_index.d,
                            'top_k': k
                        }
                
                except Exception as e:
                    print(f"Error in FAISS search: {str(e)}")
                    result['faiss_error'] = str(e)
            
            # Step 3: Context Agent (if L1_2 classification)
            if result.get('classification') == 'L1_2':
                print("\n3. Context Agent")
                print("-"*30)
                context_agent = AgentContext(query, self.load_model)
                context_result = context_agent.process_query()
                
                print(f"Context Data Type: {context_result.get('data_type', '')}")
                print(f"Location Info: {context_result.get('location_info', '')}")
                
                result.update({
                    'data_type': context_result.get('data_type'),
                    'location_details': context_result.get('location_info')
                })
            
            print("\n" + "="*50)
            print("PROCESSING COMPLETE")
            print("="*50)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in process_query: {str(e)}")
            return {
                "query": query,
                "classification": "ERROR",
                "explanation": f"Error: {str(e)}"
            }

    def run(self, query: str = None) -> Dict[str, Any]:
        """
        Run the agent system.
        
        Args:
            query (str, optional): Query string. If None, will use the query from initialization.
        
        Returns:
            Dict[str, Any]: Dictionary containing the response.
        """
        try:
            if query is None:
                query = self.query
            
            return self.process_query(query)
        except Exception as e:
            self.logger.error(f"Error in run: {str(e)}")
            return {
                "query": query, 
                "classification": "ERROR",
                "explanation": f"Error: {str(e)}"
            }

def main():
    """
    Main function to run the agent directly.
    Example usage: python3 agent.py
    """
    from memories.models.load_model import LoadModel
    from memories.core.memory import MemoryStore
    from memories.agents.agent_config import get_model_config
    
    # Get input from user
    query = input("Enter your query: ")
    instance_id = input("Enter FAISS instance ID (or press Enter to skip): ")
    
    # Initialize model with get_model_config
    load_model, _ = get_model_config(
        use_gpu=True,
        model_provider="deepseek-ai",
        deployment_type="deployment",
        model_name="deepseek-coder-1.3b-base"
    )
    
    print(f"[Agent] Model initialized")
    
    # Initialize memory store
    memory_store = MemoryStore()
    
    # Initialize and run agent
    agent = Agent(
        query=query, 
        load_model=load_model,  # Changed from model to load_model
        memory_store=memory_store,
        instance_id=instance_id if instance_id else None
    )
    
    result = agent.process_query(query)
    
    # Print results
    print("\nResults:")
    if 'similar_columns' in result:
        print("\nSimilar columns found:")
        for col in result['similar_columns']:
            print(f"\nColumn: {col['column_name']}")
            print(f"File: {col['file_name']}")
            print(f"Score: {col['similarity_score']:.3f}")
            print(f"Vector ID: {col['vector_id']}")
            print(f"Data Type: {col['data_type']}")
            
        if 'vector_search' in result:
            print(f"\nVector Search Details:")
            print(f"Query Type: {result['vector_search']['query_type']}")
            print(f"Total Vectors: {result['vector_search']['total_vectors']}")
            print(f"Vector Dimension: {result['vector_search']['dimension']}")
            print(f"Top K: {result['vector_search']['top_k']}")
    else:
        print("No similar columns found")
        
    print(f"\nClassification: {result.get('classification', '')}")
    print(f"Explanation: {result.get('explanation', '')}")

if __name__ == "__main__":
    main()

