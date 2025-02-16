def exact_match_query(parquet_file, column_name, value):
    """
    Returns a query string for an exact match on a given column.
    """
    return f"SELECT * FROM '{parquet_file}' WHERE {column_name} = '{value}';"


def like_query(parquet_file, column_name, pattern):
    """
    Returns a query string that uses the LIKE operator for pattern matching.
    """
    return f"SELECT * FROM '{parquet_file}' WHERE {column_name} LIKE '{pattern}';"


def at_coordinates_query(parquet_file, lat_col, lon_col, target_lat, target_lon):
    """
    Returns a query to find records exactly at the given coordinates.
    """
    return (
        f"SELECT * FROM '{parquet_file}' "
        f"WHERE {lat_col} = {target_lat} AND {lon_col} = {target_lon};"
    )


def within_radius_query(parquet_file, lat_col, lon_col, target_lat, target_lon, radius):
    """
    Returns a query to find records within a specified radius from a target point.
    
    Note: This query assumes ST_Distance and ST_Point functions are available in DuckDB.
    """
    return (
        f"SELECT * FROM '{parquet_file}' WHERE ST_Distance("
        f"ST_Point({lon_col}, {lat_col}), ST_Point({target_lon}, {target_lat})) <= {radius};"
    )


def nearest_query(parquet_file, lat_col, lon_col, target_lat, target_lon):
    """
    Returns a query to find the nearest record to the target point.
    """
    return (
        f"SELECT *, ST_Distance(ST_Point({lon_col}, {lat_col}), ST_Point({target_lon}, {target_lat})) AS distance "
        f"FROM '{parquet_file}' ORDER BY distance ASC LIMIT 1;"
    )


def bounding_box_query(parquet_file, lat_col, lon_col, min_lat, max_lat, min_lon, max_lon):
    """
    Returns a query to find records within a bounding box.
    """
    return (
        f"SELECT * FROM '{parquet_file}' WHERE {lat_col} BETWEEN {min_lat} AND {max_lat} "
        f"AND {lon_col} BETWEEN {min_lon} AND {max_lon};"
    )


def count_within_radius_query(parquet_file, lat_col, lon_col, target_lat, target_lon, radius):
    """
    Returns a query to count records within a specified radius.
    """
    return (
        f"SELECT COUNT(*) FROM '{parquet_file}' WHERE ST_Distance("
        f"ST_Point({lon_col}, {lat_col}), ST_Point({target_lon}, {target_lat})) < {radius};"
    )


def aggregate_query(parquet_file, group_column, lat_col, lon_col, target_lat, target_lon, radius):
    """
    Returns a query to group records by a column after applying a spatial filter.
    """
    return (
        f"SELECT {group_column}, COUNT(*) FROM '{parquet_file}' WHERE ST_Distance("
        f"ST_Point({lon_col}, {lat_col}), ST_Point({target_lon}, {target_lat})) < {radius} "
        f"GROUP BY {group_column};"
    )


def combined_filters_query(parquet_file, text_column, pattern, lat_col, lon_col, target_lat, target_lon, radius):
    """
    Returns a query combining text and spatial filters.
    """
    return (
        f"SELECT * FROM '{parquet_file}' WHERE {text_column} LIKE '{pattern}' "
        f"AND ST_Distance(ST_Point({lon_col}, {lat_col}), ST_Point({target_lon}, {target_lat})) < {radius};"
    )


def range_query(parquet_file, column_name, min_value, max_value):
    """
    Returns a query to find records where the column is within a specified range.
    """
    return f"SELECT * FROM '{parquet_file}' WHERE {column_name} BETWEEN {min_value} AND {max_value};"
