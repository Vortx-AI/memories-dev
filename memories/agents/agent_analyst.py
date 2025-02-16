from typing import Dict, Any, Optional
import os
from pathlib import Path
from memories.utils.duckdb_queries import DuckDBQueryGenerator

class AgentAnalyst:
    def __init__(self, load_model: Any):
        """
        Initialize Agent Analyst.
        
        Args:
            load_model: LLM model instance
        """
        self.load_model = load_model
        self.project_root = os.getenv("PROJECT_ROOT", "")
        
    def analyze_query(self, 
                     query: str,
                     column_info: Dict[str, Any],
                     location_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze query and generate appropriate DuckDB code.
        
        Args:
            query (str): User query
            column_info (Dict): Column information from L1 agent
            location_info (Dict, optional): Location details from context agent
        """
        try:
            print("\n[Agent Analyst] Processing Query")
            print("-" * 50)
            print(f"Query: {query}")
            print(f"Column: {column_info.get('column_name')}")
            print(f"File: {column_info.get('file_name')}")
            
            # Initialize DuckDB Query Generator
            parquet_file = os.path.join(
                self.project_root, 
                "data",
                "osm_data",
                column_info.get('file_name', '')
            )
            
            generator = DuckDBQueryGenerator(parquet_file, self.load_model)
            
            # Generate Python code
            print("\nGenerating DuckDB query code...")
            code = generator.generate_query_code(
                query=query,
                column_info=column_info,
                location_info=location_info
            )
            
            # Execute generated code
            print("\nExecuting generated code...")
            results = generator.execute_generated_code(code)
            
            return {
                "status": "success",
                "query": query,
                "generated_code": code,
                "results": results,
                "row_count": len(results) if results is not None else 0
            }
            
        except Exception as e:
            print(f"[Agent Analyst] Error: {str(e)}")
            return {
                "status": "error",
                "query": query,
                "error": str(e)
            }

def main():
    """Example usage of Agent Analyst"""
    from memories.models.load_model import LoadModel
    
    # Initialize model
    load_model = LoadModel()
    
    # Example inputs
    query = "find hospitals near bangalore"
    column_info = {
        "column_name": "amenity",
        "file_name": "india_points_processed.parquet",
        "distance": 0.7762
    }
    location_info = {
        "location": "bangalore",
        "coordinates": [12.9716, 77.5946],
        "radius": 5000
    }
    
    # Initialize analyst
    analyst = AgentAnalyst(load_model)
    
    # Process query
    result = analyst.analyze_query(
        query=query,
        column_info=column_info,
        location_info=location_info
    )
    
    # Print results
    print("\nAnalysis Results:")
    print("=" * 50)
    if result["status"] == "success":
        print(f"\nGenerated Code:\n{result['generated_code']}")
        print(f"\nResults DataFrame:\n{result['results']}")
        print(f"\nTotal Rows: {result['row_count']}")
    else:
        print(f"Error: {result['error']}")

def fetch_data():
    """
    Find parks within Bangalore bounds
    """
    try:
        conn = duckdb.connect(':memory:')
        query = """
            SELECT 
                leisure,
                name,
                ST_X(geom) as longitude,
                ST_Y(geom) as latitude,
                ST_Area(geom) as area_sqm
            FROM parquet_scan('india_points_processed.parquet')
            WHERE 
                leisure = 'park'
                AND ST_X(geom) BETWEEN 77.4850 AND 77.7480
                AND ST_Y(geom) BETWEEN 12.8539 AND 13.0730
            ORDER BY area_sqm DESC
            LIMIT 100
        """
        return conn.execute(query).fetchdf()
    except Exception as e:
        print(f"Error: {str(e)}")
        return pd.DataFrame()

if __name__ == "__main__":
    main()
