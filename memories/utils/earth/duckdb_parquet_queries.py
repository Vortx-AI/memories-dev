def exact_match_query(parquet_file, column_name, value, aoi=None):
    """
    Returns a query string for an exact match with optional AOI filtering.
    Assumes column_name is a Boolean column.
    """
    bool_value = str(value).lower() == 'true'
    base_query = (
        f"SELECT *, "
        f"ST_X(geom) as longitude, "
        f"ST_Y(geom) as latitude "
        f"FROM '{parquet_file}' WHERE {column_name} = {bool_value}"
    )
    
    if aoi is not None:
        return f"{base_query} AND ST_Intersects(geom, ST_GeomFromText('{aoi}'));"
    return f"{base_query};"


def like_query(parquet_file, column_name, pattern, aoi=None):
    """
    Returns a query string that uses the LIKE operator for pattern matching.
    """
    base_query = f"SELECT * FROM '{parquet_file}' WHERE {column_name} LIKE '{pattern}'"
    
    if aoi is not None:
        return f"{base_query} AND ST_Intersects(geom, ST_GeomFromText('{aoi}'));"
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
    Returns a query to find records within radius and matching boolean column value.
    Radius is in kilometers.
    """
    bool_value = str(value).lower() == 'true'
    target_point = f"ST_Point({target_lon}, {target_lat})"
    return (
        f"SELECT *, "
        f"ST_X(ST_GeomFromWKB(geom)) as longitude, "
        f"ST_Y(ST_GeomFromWKB(geom)) as latitude, "
        f"ST_Distance(ST_GeomFromWKB(geom), {target_point}) as distance_km "
        f"FROM '{parquet_file}' "
        f"WHERE {column_name} = {bool_value} "
        f"AND ST_DWithin(ST_GeomFromWKB(geom), {target_point}, {radius}) "
        f"ORDER BY distance_km ASC;"
    )


def get_geometry_column(parquet_file):
    """
    Determine which geometry column exists in the parquet file.
    Returns 'geometry' or 'geom' based on which exists.
    """
    return "CASE WHEN EXISTS(SELECT 1 FROM '{0}' LIMIT 1) THEN " \
           "CASE WHEN '{0}' LIKE '%geometry%' THEN 'geometry' ELSE 'geom' END " \
           "END".format(parquet_file)


def nearest_query(parquet_file, column_name, value, aoi, limit=5):
    """
    Returns a query to find the nearest records to AOI centroid matching boolean column value.
    """
    bool_value = str(value).lower() == 'true'
    return (
        f"WITH geom_col AS (SELECT {get_geometry_column(parquet_file)} as col_name), "
        f"data AS ("
        f"  SELECT *, "
        f"  ST_X(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END)) as longitude, "
        f"  ST_Y(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END)) as latitude, "
        f"  ST_Distance(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END), "
        f"             ST_Centroid(ST_GeomFromText('{aoi}'))) as distance_km "
        f"  FROM '{parquet_file}' CROSS JOIN geom_col "
        f"  WHERE {column_name} = {bool_value} "
        f") "
        f"SELECT * FROM data "
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
    Returns a query to count records within radius and matching boolean column value.
    """
    bool_value = str(value).lower() == 'true'
    target_point = f"ST_Point({target_lon}, {target_lat})"
    return (
        f"WITH distances AS ("
        f"  SELECT *, "
        f"  ST_X(ST_GeomFromWKB(geom)) as longitude, "
        f"  ST_Y(ST_GeomFromWKB(geom)) as latitude, "
        f"  ST_Distance(ST_GeomFromWKB(geom), {target_point}) as distance_km "
        f"  FROM '{parquet_file}' "
        f"  WHERE {column_name} = {bool_value}"
        f") "
        f"SELECT COUNT(*) as count, "
        f"MIN(distance_km) as min_distance_km, "
        f"MAX(distance_km) as max_distance_km "
        f"FROM distances "
        f"WHERE distance_km <= {radius};"
    )


def aggregate_query(parquet_file, group_column, filter_column, value, aoi):
    """
    Returns a query to group records after applying boolean filter and spatial constraints.
    """
    bool_value = str(value).lower() == 'true'
    return (
        f"WITH distances AS ("
        f"  SELECT *, "
        f"  ST_X(geom) as longitude, "
        f"  ST_Y(geom) as latitude, "
        f"  ST_Distance(geom, ST_Centroid(ST_GeomFromText('{aoi}'))) as distance_km "
        f"  FROM '{parquet_file}' "
        f"  WHERE {filter_column} = {bool_value}"
        f"  AND ST_Intersects(geom, ST_GeomFromText('{aoi}'))"
        f") "
        f"SELECT {group_column}, "
        f"COUNT(*) as count, "
        f"MIN(distance_km) as min_distance_km, "
        f"MAX(distance_km) as max_distance_km "
        f"FROM distances "
        f"GROUP BY {group_column} "
        f"ORDER BY min_distance_km ASC;"
    )


def combined_filters_query(parquet_file, column_name, value, pattern_column, pattern, aoi):
    """
    Returns a query combining boolean filter, text pattern, and spatial filters.
    """
    bool_value = str(value).lower() == 'true'
    return (
        f"SELECT *, "
        f"ST_X(geom) as longitude, "
        f"ST_Y(geom) as latitude, "
        f"ST_Distance(geom, ST_Centroid(ST_GeomFromText('{aoi}'))) as distance_km "
        f"FROM '{parquet_file}' "
        f"WHERE {column_name} = {bool_value} "
        f"AND {pattern_column} LIKE '{pattern}' "
        f"AND ST_Intersects(geom, ST_GeomFromText('{aoi}')) "
        f"ORDER BY distance_km ASC;"
    )


def range_query(parquet_file, range_column, min_value, max_value, filter_column, value, aoi=None):
    """
    Returns a query for records within a range and matching boolean column value.
    """
    bool_value = str(value).lower() == 'true'
    base_query = (
        f"SELECT *, "
        f"ST_X(geom) as longitude, "
        f"ST_Y(geom) as latitude "
        f"FROM '{parquet_file}' "
        f"WHERE {range_column} BETWEEN {min_value} AND {max_value} "
        f"AND {filter_column} = {bool_value}"
    )
    
    if aoi is not None:
        return (
            f"SELECT *, "
            f"ST_Distance(geom, ST_Centroid(ST_GeomFromText('{aoi}'))) as distance_km "
            f"FROM ({base_query}) "
            f"WHERE ST_Intersects(geom, ST_GeomFromText('{aoi}')) "
            f"ORDER BY distance_km ASC;"
        )
    
    return f"{base_query};"


def within_area_query(parquet_file, column_name, value, aoi):
    """
    Returns a query to find records within AOI and matching boolean column value.
    """
    bool_value = str(value).lower() == 'true'
    return (
        f"WITH geom_col AS (SELECT {get_geometry_column(parquet_file)} as col_name), "
        f"data AS ("
        f"  SELECT *, "
        f"  ST_X(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END)) as longitude, "
        f"  ST_Y(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END)) as latitude, "
        f"  ST_Distance(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END), "
        f"             ST_Centroid(ST_GeomFromText('{aoi}'))) as distance_km "
        f"  FROM '{parquet_file}' CROSS JOIN geom_col "
        f"  WHERE {column_name} = {bool_value} "
        f"  AND ST_Intersects(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END), "
        f"                    ST_GeomFromText('{aoi}'))"
        f") "
        f"SELECT * FROM data "
        f"ORDER BY distance_km ASC;"
    )


def count_within_area_query(parquet_file, column_name, value, aoi):
    """
    Returns a query to count records within AOI and matching boolean column value.
    """
    bool_value = str(value).lower() == 'true'
    return (
        f"WITH geom_col AS (SELECT {get_geometry_column(parquet_file)} as col_name), "
        f"distances AS ("
        f"  SELECT *, "
        f"  ST_X(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END)) as longitude, "
        f"  ST_Y(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END)) as latitude, "
        f"  ST_Distance(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END), "
        f"             ST_Centroid(ST_GeomFromText('{aoi}'))) as distance_km "
        f"  FROM '{parquet_file}' CROSS JOIN geom_col "
        f"  WHERE {column_name} = {bool_value} "
        f"  AND ST_Intersects(ST_GeomFromWKB(CASE WHEN col_name = 'geometry' THEN geometry ELSE geom END), "
        f"                    ST_GeomFromText('{aoi}'))"
        f") "
        f"SELECT COUNT(*) as count, "
        f"MIN(distance_km) as min_distance_km, "
        f"MAX(distance_km) as max_distance_km "
        f"FROM distances;"
    )
