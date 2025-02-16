import pandas as pd
import pyarrow.parquet as pq
import numpy as np
try:
    import cudf
    import cupy as cp
    HAS_GPU = True
except ImportError:
    HAS_GPU = False
    print("GPU libraries not found. Using CPU processing.")

def process_points_data(use_gpu: bool = True):
    """
    Process points data with GPU acceleration if available.
    
    Args:
        use_gpu (bool): Whether to use GPU acceleration
    
    This function:
    1. Reads parquet file into GPU memory if available
    2. Performs vectorized operations on GPU
    3. Creates boolean feature columns
    4. Returns processed DataFrame
    """
    if use_gpu and not HAS_GPU:
        print("GPU libraries not found. Falling back to CPU processing.")
        use_gpu = False
    
    # Read the parquet file
    print("Reading points data...")
    if use_gpu:
        df = cudf.read_parquet('india_points.parquet')
        print("Data loaded to GPU memory")
    else:
        df = pq.read_table('india_points.parquet').to_pandas()
    
    # Create a copy to avoid fragmentation
    df = df.copy()
    
    # Add geometry_type column
    print("Adding geometry_type column...")
    df['geometry_type'] = 'point'
    
    # Get unique values using GPU or CPU
    print("Getting unique values...")
    if use_gpu:
        unique_values = cp.unique(cp.concatenate([
            df['barrier'].dropna().values.get(),
            df['highway'].dropna().values.get(),
            df['man_made'].dropna().values.get()
        ]))
    else:
        unique_values = np.unique(np.concatenate([
            df['barrier'].dropna().unique(),
            df['highway'].dropna().unique(),
            df['man_made'].dropna().unique()
        ]))
    
    # Create new columns using GPU/CPU vectorized operations
    print("Creating new columns...")
    
    if use_gpu:
        # GPU operations
        barrier_mask = df['barrier'].fillna('').values.reshape(-1, 1) == unique_values
        highway_mask = df['highway'].fillna('').values.reshape(-1, 1) == unique_values
        man_made_mask = df['man_made'].fillna('').values.reshape(-1, 1) == unique_values
        
        # Combine masks on GPU
        combined_mask = barrier_mask | highway_mask | man_made_mask
        
        # Create new DataFrame on GPU
        new_data = cudf.DataFrame(
            combined_mask,
            columns=unique_values,
            index=df.index
        )
    else:
        # CPU operations (same as before)
        barrier_mask = df['barrier'].fillna('').values[:, None] == unique_values
        highway_mask = df['highway'].fillna('').values[:, None] == unique_values
        man_made_mask = df['man_made'].fillna('').values[:, None] == unique_values
        combined_mask = barrier_mask | highway_mask | man_made_mask
        new_data = pd.DataFrame(
            combined_mask,
            columns=unique_values,
            index=df.index
        )
    
    # Concatenate columns
    print("Concatenating columns...")
    if use_gpu:
        df_new = cudf.concat([df, new_data], axis=1)
    else:
        df_new = pd.concat([df, new_data], axis=1)
    
    # Save the processed data
    print("Saving processed data...")
    if use_gpu:
        df_new.to_parquet('india_points_processed.parquet')
        # Convert to pandas for memory usage calculation
        df_new_pd = df_new.to_pandas()
    else:
        df_new.to_parquet('india_points_processed.parquet')
        df_new_pd = df_new
    
    print("Processing complete!")
    
    # Print column information
    print("\nColumn Information:")
    print(f"Total columns: {len(df_new.columns)}")
    print(f"Original columns: {list(df.columns)}")
    print(f"New feature columns: {list(new_data.columns)}")
    print(f"Geometry type column added: 'geometry_type'")
    
    return df_new_pd

if __name__ == "__main__":
    try:
        # Try GPU processing first
        df_processed = process_points_data(use_gpu=True)
        
        print(f"\nProcessed DataFrame shape: {df_processed.shape}")
        
        # Print memory usage
        memory_usage = df_processed.memory_usage(deep=True).sum() / 1024**2
        print(f"Memory usage: {memory_usage:.2f} MB")
        
        # Print processing summary
        print("\nProcessing Summary:")
        print(f"Original columns: {len(df_processed.columns) - len(df_processed.select_dtypes(include=['bool']).columns) - 1}")
        print(f"New boolean columns: {len(df_processed.select_dtypes(include=['bool']).columns)}")
        print(f"Total rows: {len(df_processed)}")
        
        # Print first few rows
        print("\nFirst few rows of processed data:")
        bool_columns = df_processed.select_dtypes(include=['bool']).columns
        print(df_processed[['geometry_type'] + list(bool_columns)][:2])
        
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        print("Falling back to CPU processing...")
        # Try CPU processing if GPU fails
        df_processed = process_points_data(use_gpu=False) 