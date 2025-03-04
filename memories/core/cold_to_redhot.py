def process_parquet_file(self, file_path):
    """Process a parquet file and extract column metadata."""
    try:
        # Read parquet metadata
        pf = pq.ParquetFile(file_path)
        schema = pf.schema
        
        # Get all column names including geometry columns
        all_columns = schema.names
        
        # Look for geometry columns
        geometry_columns = [col for col in all_columns 
                          if col.lower() in ['geom', 'geometry', 'the_geom', 'shape']]
        
        metadata_entries = []
        for i, col in enumerate(all_columns):
            field = schema.field(i)
            metadata = {
                'file_path': file_path,
                'column_name': col,
                'dtype': str(field.type),
                'all_columns': all_columns,
                'type': 'column',
                'geometry_columns': geometry_columns  # Add geometry columns to metadata
            }
            metadata_entries.append(metadata)
            
        return metadata_entries
        
    except Exception as e:
        logger.error(f"Error processing parquet file {file_path}: {e}")
        return []