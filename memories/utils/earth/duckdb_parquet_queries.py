def exact_match_query(parquet_file, geometry_column, geometry_type, column_name, value):
    """
    Returns a query string for an exact match on both geometry and specified column.
    """
    return f"SELECT * FROM '{parquet_file}' WHERE {column_name} = '{value}' AND {geometry_column} IS NOT NULL;"


def like_query(parquet_file, geometry_column, geometry_type, column_name, pattern):
    """
    Returns a query string that uses the LIKE operator for pattern matching along with geometry validation.
    """
    return f"SELECT * FROM '{parquet_file}' WHERE {column_name} LIKE '{pattern}' AND {geometry_column} IS NOT NULL;"


def at_coordinates_query(parquet_file, geometry_column, geometry_type, column_name, value, target_lat, target_lon):
    """
    Returns a query to find records at given coordinates with column filter.
    """
    return (
        f"SELECT * FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' AND "
        f"ST_Y({geometry_column}) = {target_lat} AND ST_X({geometry_column}) = {target_lon};"
    )


def within_radius_query(parquet_file, geometry_column, geometry_type, column_name, value, target_lat, target_lon, radius):
    """
    Returns a query to find records within radius and matching column value.
    """
    return (
        f"SELECT * FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' AND ST_DWithin("
        f"{geometry_column}, ST_Point({target_lon}, {target_lat}), {radius});"
    )


def nearest_query(parquet_file, geometry_column, geometry_type, column_name, value, target_lat, target_lon):
    """
    Returns a query to find the nearest record matching column value.
    """
    return (
        f"SELECT *, ST_Distance({geometry_column}, ST_Point({target_lon}, {target_lat})) AS distance "
        f"FROM '{parquet_file}' WHERE {column_name} = '{value}' "
        f"ORDER BY distance ASC LIMIT 1;"
    )


def bounding_box_query(parquet_file, geometry_column, geometry_type, column_name, value, min_lat, max_lat, min_lon, max_lon):
    """
    Returns a query to find records within bounding box and matching column value.
    """
    return (
        f"SELECT * FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' AND "
        f"ST_Y({geometry_column}) BETWEEN {min_lat} AND {max_lat} AND "
        f"ST_X({geometry_column}) BETWEEN {min_lon} AND {max_lon};"
    )


def count_within_radius_query(parquet_file, geometry_column, geometry_type, column_name, value, target_lat, target_lon, radius):
    """
    Returns a query to count records within radius and matching column value.
    """
    return (
        f"SELECT COUNT(*) FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' AND ST_DWithin("
        f"{geometry_column}, ST_Point({target_lon}, {target_lat}), {radius});"
    )


def aggregate_query(parquet_file, geometry_column, geometry_type, group_column, filter_column, value, target_lat, target_lon, radius):
    """
    Returns a query to group records after applying both spatial and column filters.
    """
    return (
        f"SELECT {group_column}, COUNT(*) FROM '{parquet_file}' "
        f"WHERE {filter_column} = '{value}' AND ST_DWithin("
        f"{geometry_column}, ST_Point({target_lon}, {target_lat}), {radius}) "
        f"GROUP BY {group_column};"
    )


def combined_filters_query(parquet_file, geometry_column, geometry_type, column_name, value, pattern_column, pattern, target_lat, target_lon, radius):
    """
    Returns a query combining text pattern, column value, and spatial filters.
    """
    return (
        f"SELECT * FROM '{parquet_file}' "
        f"WHERE {column_name} = '{value}' AND {pattern_column} LIKE '{pattern}' "
        f"AND ST_DWithin({geometry_column}, ST_Point({target_lon}, {target_lat}), {radius});"
    )


def range_query(parquet_file, geometry_column, geometry_type, range_column, min_value, max_value, filter_column, value):
    """
    Returns a query for records within a range and matching column value.
    """
    return (
        f"SELECT * FROM '{parquet_file}' "
        f"WHERE {range_column} BETWEEN {min_value} AND {max_value} "
        f"AND {filter_column} = '{value}' AND {geometry_column} IS NOT NULL;"
    )
