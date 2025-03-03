"""
Memory retrieval functionality for querying cold memory storage.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class MemoryRetrieval:
    """Memory retrieval class for querying cold memory storage."""
    
    def __init__(self, cold_memory):
        """Initialize memory retrieval.
        
        Args:
            cold_memory: ColdMemory instance to query from
        """
        self.cold = cold_memory
        self.logger = logging.getLogger(__name__)

    def list_available_data(self) -> List[Dict[str, Any]]:
        """List all available data tables and their metadata.
        
        Returns:
            List of dictionaries containing table information:
                - table_name: Name of the table
                - file_path: Original parquet file path
                - theme: Theme tag if provided during import
                - tag: Additional tag if provided during import
                - num_rows: Number of rows
                - num_columns: Number of columns
                - schema: Column names and types
        """
        return self.cold.list_tables()

    def get_schema(self, table_name: str) -> Optional[Dict[str, str]]:
        """Get schema for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary mapping column names to their types, or None if table not found
        """
        return self.cold.get_table_schema(table_name)

    def preview_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Preview data from a specific table.
        
        Args:
            table_name: Name of the table to preview
            limit: Number of rows to preview (default: 5)
            
        Returns:
            pandas DataFrame with preview rows
        """
        return self.cold.get_table_preview(table_name, limit)

    def search(self, 
              conditions: Dict[str, Any], 
              tables: Optional[List[str]] = None,
              limit: int = 100
    ) -> pd.DataFrame:
        """Search across tables using specified conditions.
        
        Args:
            conditions: Dictionary of column-value pairs to search for
            tables: Optional list of specific table names to search in
            limit: Maximum number of results to return (default: 100)
            
        Returns:
            pandas DataFrame with matching records
        """
        return self.cold.search(conditions, tables, limit)

    def query(self, sql_query: str) -> pd.DataFrame:
        """Execute a SQL query across all imported data.
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            pandas DataFrame with query results
        """
        return self.cold.query(sql_query)

    def get_data_by_theme(self, theme: str, limit: int = 100) -> pd.DataFrame:
        """Get data from tables with a specific theme.
        
        Args:
            theme: Theme to filter by
            limit: Maximum number of results to return (default: 100)
            
        Returns:
            pandas DataFrame with matching records
        """
        try:
            # Get tables with matching theme
            tables = self.cold.list_tables()
            theme_tables = [t["table_name"] for t in tables if t["theme"] == theme]
            
            if not theme_tables:
                self.logger.warning(f"No tables found with theme: {theme}")
                return pd.DataFrame()
            
            # Build query to union all matching tables
            queries = [f"SELECT *, '{table}' as source_table FROM {table}" for table in theme_tables]
            full_query = f"""
                SELECT * FROM (
                    {" UNION ALL ".join(queries)}
                ) combined_results
                LIMIT {limit}
            """
            
            return self.cold.query(full_query)
            
        except Exception as e:
            self.logger.error(f"Error getting data for theme {theme}: {e}")
            return pd.DataFrame()

    def get_data_by_tag(self, tag: str, limit: int = 100) -> pd.DataFrame:
        """Get data from tables with a specific tag.
        
        Args:
            tag: Tag to filter by
            limit: Maximum number of results to return (default: 100)
            
        Returns:
            pandas DataFrame with matching records
        """
        try:
            # Get tables with matching tag
            tables = self.cold.list_tables()
            tag_tables = [t["table_name"] for t in tables if t["tag"] == tag]
            
            if not tag_tables:
                self.logger.warning(f"No tables found with tag: {tag}")
                return pd.DataFrame()
            
            # Build query to union all matching tables
            queries = [f"SELECT *, '{table}' as source_table FROM {table}" for table in tag_tables]
            full_query = f"""
                SELECT * FROM (
                    {" UNION ALL ".join(queries)}
                ) combined_results
                LIMIT {limit}
            """
            
            return self.cold.query(full_query)
            
        except Exception as e:
            self.logger.error(f"Error getting data for tag {tag}: {e}")
            return pd.DataFrame()

    def get_data_by_date_range(
        self,
        start_date: str,
        end_date: str,
        date_column: str = "timestamp",
        limit: int = 100
    ) -> pd.DataFrame:
        """Get data within a specific date range.
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            date_column: Name of the date column to filter on (default: "timestamp")
            limit: Maximum number of results to return (default: 100)
            
        Returns:
            pandas DataFrame with matching records
        """
        try:
            # Get all tables
            tables = self.cold.list_tables()
            if not tables:
                self.logger.warning("No tables available")
                return pd.DataFrame()
            
            # Build query to union all tables with date filter
            queries = []
            for table in tables:
                table_name = table["table_name"]
                # Check if the date column exists in this table
                schema = table["schema"]
                if date_column in schema:
                    queries.append(f"""
                        SELECT *, '{table_name}' as source_table 
                        FROM {table_name}
                        WHERE {date_column} BETWEEN '{start_date}' AND '{end_date}'
                    """)
            
            if not queries:
                self.logger.warning(f"No tables found with date column: {date_column}")
                return pd.DataFrame()
            
            full_query = f"""
                SELECT * FROM (
                    {" UNION ALL ".join(queries)}
                ) combined_results
                LIMIT {limit}
            """
            
            return self.cold.query(full_query)
            
        except Exception as e:
            self.logger.error(f"Error getting data for date range: {e}")
            return pd.DataFrame()

    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get statistics for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary containing table statistics:
                - row_count: Total number of rows
                - column_stats: Per-column statistics (min, max, avg, etc.)
        """
        try:
            # Get basic table info
            schema = self.cold.get_table_schema(table_name)
            if not schema:
                raise ValueError(f"Table not found: {table_name}")
            
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            row_count = self.cold.query(count_query).iloc[0]['row_count']
            
            # Get column statistics
            column_stats = {}
            for column, dtype in schema.items():
                if 'int' in dtype.lower() or 'float' in dtype.lower() or 'double' in dtype.lower():
                    stats_query = f"""
                        SELECT 
                            MIN({column}) as min_value,
                            MAX({column}) as max_value,
                            AVG({column}) as avg_value,
                            COUNT(DISTINCT {column}) as unique_count
                        FROM {table_name}
                    """
                    stats = self.cold.query(stats_query).to_dict('records')[0]
                    column_stats[column] = stats
                else:
                    # For non-numeric columns, just get unique count
                    stats_query = f"""
                        SELECT COUNT(DISTINCT {column}) as unique_count
                        FROM {table_name}
                    """
                    stats = {'unique_count': self.cold.query(stats_query).iloc[0]['unique_count']}
                    column_stats[column] = stats
            
            return {
                'row_count': row_count,
                'column_stats': column_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats for table {table_name}: {e}")
            return {} 