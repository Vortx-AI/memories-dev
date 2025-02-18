import os
from pathlib import Path
import cudf
import pyarrow as pa
import pyarrow.parquet as pq

def read_parquet_with_conversion(file_path: str):
    """
    Attempt to read a parquet file with cuDF. If that fails (typically due
    to dictionary-encoded columns), fall back to reading with PyArrow, converting
    dictionary columns to strings, and then convert to a cuDF DataFrame.
    """
    try:
        df = cudf.read_parquet(file_path)
        return df
    except Exception as e:
        print(f"cuDF failed for {file_path} with error:\n  {e}\nFalling back to PyArrow.")
        table = pq.read_table(file_path)
        # Convert dictionary-encoded columns to string.
        new_arrays = []
        for col in table.column_names:
            arr = table[col]
            if pa.types.is_dictionary(arr.type):
                # Cast dictionary column to string
                arr = arr.cast(pa.string())
            new_arrays.append(arr)
        new_table = pa.Table.from_arrays(new_arrays, names=table.column_names)
        df = cudf.DataFrame.from_arrow(new_table)
        return df

def add_geom_to_parquet(file_path: str):
    """
    Load a parquet file (using our read_parquet_with_conversion helper), create a new
    'geom' column using the bounding box columns, and write the file back.
    
    The 'geom' column will be the well-known text (WKT) for the bounding box polygon:
       "POLYGON ((xmin ymin, xmax ymin, xmax ymax, xmin ymax, xmin ymin))"
    """
    file_path = Path(file_path)
    print(f"Processing file: {file_path}")
    try:
        df = read_parquet_with_conversion(file_path)
        # Ensure required bounding box columns exist
        required_cols = ['xmin', 'xmax', 'ymin', 'ymax']
        if not all(col in df.columns for col in required_cols):
            print(f"Skipping {file_path} since one or more required columns are missing.")
            return

        # Build the 'geom' column as a WKT polygon string.
        # Convert all coordinates to string in case they are not already.
        df['geom'] = (
            "POLYGON ((" +
            df['xmin'].astype('str') + " " + df['ymin'].astype('str') + ", " +
            df['xmax'].astype('str') + " " + df['ymin'].astype('str') + ", " +
            df['xmax'].astype('str') + " " + df['ymax'].astype('str') + ", " +
            df['xmin'].astype('str') + " " + df['ymax'].astype('str') + ", " +
            df['xmin'].astype('str') + " " + df['ymin'].astype('str') +
            "))"
        )

        # Write the modified DataFrame back to parquet (overwriting).
        df.to_parquet(file_path)
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def process_all_parquet_files(root_folder: str):
    """
    Recursively search for all parquet files under the given root folder, adding
    the new geometry column to each file.
    """
    root_path = Path(root_folder)
    print(f"Searching for parquet files in: {root_path}")
    for parquet_file in root_path.rglob("*.parquet"):
        add_geom_to_parquet(parquet_file)

if __name__ == "__main__":
    # Set the folder to your target folder -- in this case, /home/jaya/geo_memories.
    folder = "/home/jaya/geo_memories"
    process_all_parquet_files(folder) 