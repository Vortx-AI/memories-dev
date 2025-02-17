def exact_match_query(parquet_file, column_name, value, lat=None, lon=None):
    """
    Returns a query string for an exact match with optional coordinate filtering.
    
    Args:
        parquet_file (str): Path to parquet file
        column_name (str): Column name to match
        value (str): Value to match
        lat (float, optional): Latitude for coordinate filtering
        lon (float, optional): Longitude for coordinate filtering
    """
    base_query = f"SELECT * FROM '{parquet_file}' WHERE {column_name} = '{value}'"
    
    if lat is not None and lon is not None:
        return f"{base_query} AND lat = {lat} AND lon = {lon};"
    return f"{base_query};"


def like_query(parquet_file, column_name, pattern, lat=None, lon=None):
    """
    Returns a query string that uses the LIKE operator for pattern matching.
    """
    base_query = f"SELECT * FROM '{parquet_file}' WHERE {column_name} LIKE '{pattern}'"
    
    if lat is not None and lon is not None:
        return f"{base_query} AND lat = {lat} AND lon = {lon};"
    return f"{base_query};"


def at_coordinates_query(parquet_file, column_name, value, target_lat, target_lon):
    """
    Returns a query to find records at given coordinates with column filter.
    """
    return (
        f"SELECT *, "
        f"SQRT(POWER(lat - {target_lat}, 2) + POWER(lon - {target_lon}, 2)) as distance "
        f"FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' AND "
        f"lat = {target_lat} AND lon = {target_lon};"
    )


def within_radius_query(parquet_file, column_name, value, target_lat, target_lon, radius):
    """
    Returns a query to find records within radius and matching column value.
    Radius is in kilometers.
    """
    return (
        f"SELECT *, "
        f"6371 * 2 * ASIN(SQRT("
        f"POWER(SIN(RADIANS({target_lat} - lat) / 2), 2) + "
        f"COS(RADIANS(lat)) * COS(RADIANS({target_lat})) * "
        f"POWER(SIN(RADIANS({target_lon} - lon) / 2), 2)"
        f")) as distance_km "
        f"FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' "
        f"HAVING distance_km <= {radius} "
        f"ORDER BY distance_km ASC;"
    )


def nearest_query(parquet_file, column_name, value, target_lat, target_lon, limit=5):
    """
    Returns a query to find the nearest records matching column value.
    
    Args:
        limit (int): Number of nearest records to return (default: 5)
    """
    return (
        f"SELECT *, "
        f"6371 * 2 * ASIN(SQRT("
        f"POWER(SIN(RADIANS({target_lat} - lat) / 2), 2) + "
        f"COS(RADIANS(lat)) * COS(RADIANS({target_lat})) * "
        f"POWER(SIN(RADIANS({target_lon} - lon) / 2), 2)"
        f")) as distance_km "
        f"FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' "
        f"ORDER BY distance_km ASC "
        f"LIMIT {limit};"
    )


def bounding_box_query(parquet_file, column_name, value, min_lat, max_lat, min_lon, max_lon):
    """
    Returns a query to find records within bounding box and matching column value.
    """
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    
    return (
        f"SELECT *, "
        f"6371 * 2 * ASIN(SQRT("
        f"POWER(SIN(RADIANS({center_lat} - lat) / 2), 2) + "
        f"COS(RADIANS(lat)) * COS(RADIANS({center_lat})) * "
        f"POWER(SIN(RADIANS({center_lon} - lon) / 2), 2)"
        f")) as distance_to_center_km "
        f"FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' AND "
        f"lat BETWEEN {min_lat} AND {max_lat} AND "
        f"lon BETWEEN {min_lon} AND {max_lon} "
        f"ORDER BY distance_to_center_km ASC;"
    )


def count_within_radius_query(parquet_file, column_name, value, target_lat, target_lon, radius):
    """
    Returns a query to count records within radius and matching column value.
    Radius is in kilometers.
    """
    return (
        f"WITH distances AS ("
        f"  SELECT *, "
        f"  6371 * 2 * ASIN(SQRT("
        f"    POWER(SIN(RADIANS({target_lat} - lat) / 2), 2) + "
        f"    COS(RADIANS(lat)) * COS(RADIANS({target_lat})) * "
        f"    POWER(SIN(RADIANS({target_lon} - lon) / 2), 2)"
        f"  )) as distance_km "
        f"  FROM '{parquet_file}' "
        f"  WHERE {column_name} = '{value}'"
        f") "
        f"SELECT COUNT(*) as count, "
        f"MIN(distance_km) as min_distance_km, "
        f"MAX(distance_km) as max_distance_km "
        f"FROM distances "
        f"WHERE distance_km <= {radius};"
    )


def aggregate_query(parquet_file, group_column, filter_column, value, target_lat, target_lon, radius):
    """
    Returns a query to group records after applying both spatial and column filters.
    Radius is in kilometers.
    """
    return (
        f"WITH distances AS ("
        f"  SELECT *, "
        f"  6371 * 2 * ASIN(SQRT("
        f"    POWER(SIN(RADIANS({target_lat} - lat) / 2), 2) + "
        f"    COS(RADIANS(lat)) * COS(RADIANS({target_lat})) * "
        f"    POWER(SIN(RADIANS({target_lon} - lon) / 2), 2)"
        f"  )) as distance_km "
        f"  FROM '{parquet_file}' "
        f"  WHERE {filter_column} = '{value}'"
        f") "
        f"SELECT {group_column}, "
        f"COUNT(*) as count, "
        f"MIN(distance_km) as min_distance_km, "
        f"MAX(distance_km) as max_distance_km "
        f"FROM distances "
        f"WHERE distance_km <= {radius} "
        f"GROUP BY {group_column} "
        f"ORDER BY min_distance_km ASC;"
    )


def combined_filters_query(parquet_file, column_name, value, pattern_column, pattern, target_lat, target_lon, radius):
    """
    Returns a query combining text pattern, column value, and spatial filters.
    Radius is in kilometers.
    """
    return (
        f"SELECT *, "
        f"6371 * 2 * ASIN(SQRT("
        f"POWER(SIN(RADIANS({target_lat} - lat) / 2), 2) + "
        f"COS(RADIANS(lat)) * COS(RADIANS({target_lat})) * "
        f"POWER(SIN(RADIANS({target_lon} - lon) / 2), 2)"
        f")) as distance_km "
        f"FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' "
        f"AND {pattern_column} LIKE '{pattern}' "
        f"HAVING distance_km <= {radius} "
        f"ORDER BY distance_km ASC;"
    )


def range_query(parquet_file, range_column, min_value, max_value, filter_column, value, target_lat=None, target_lon=None):
    """
    Returns a query for records within a range and matching column value.
    """
    base_query = (
        f"SELECT * "
        f"FROM '{parquet_file}' "
        f"WHERE {range_column} BETWEEN {min_value} AND {max_value} "
        f"AND {filter_column} = '{value}'"
    )
    
    if target_lat is not None and target_lon is not None:
        return (
            f"SELECT *, "
            f"6371 * 2 * ASIN(SQRT("
            f"POWER(SIN(RADIANS({target_lat} - lat) / 2), 2) + "
            f"COS(RADIANS(lat)) * COS(RADIANS({target_lat})) * "
            f"POWER(SIN(RADIANS({target_lon} - lon) / 2), 2)"
            f")) as distance_km "
            f"FROM ({base_query}) "
            f"ORDER BY distance_km ASC;"
        )
    
    return f"{base_query};"
