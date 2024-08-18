import os
from datetime import datetime

import yaml
from ohsome import OhsomeClient
import geopandas as gpd


def query_ohsome_api_extract(client: OhsomeClient, df: gpd.GeoDataFrame, time: str, filter: str, properties: bool) -> gpd.GeoDataFrame:
    district_df = gpd.GeoDataFrame(geometry=gpd.GeoSeries(df.geometry))

    if properties:
        response = client.elements.geometry.post(
            bpolys=district_df,
            time=time,
            filter=filter,
            properties="tags",
        )
    else:
        response = client.elements.geometry.post(
            bpolys=district_df,
            time=time,
            filter=filter,
        )

    results_df = response.as_dataframe()

    results_df["geometry"] = results_df.geometry

    return results_df

def query_ohsome_api_count(client: OhsomeClient, df: gpd.GeoDataFrame, time: str, filter: str = None) -> int:
    if time is None:
        time = datetime.now().strftime("%Y-%m-%d")
    district_df = gpd.GeoDataFrame(geometry=gpd.GeoSeries(df.geometry))

    response = client.elements.count.post(
        bpolys=district_df,
        time=time,
        filter=filter,
    )

    return response.data["result"][0]["value"]

def get_road_data(client: OhsomeClient, df: gpd.GeoDataFrame, time: str = None) -> gpd.GeoDataFrame:
    if time is None:
        time = datetime.now().strftime("%Y-%m-%d")
    return query_ohsome_api_extract(client, df, time, "highway=*", True)


def get_row_by_column(gdf, column_name, value, bus_isochrone: bool = False):
    """
    Returns a row from the GeoDataFrame based on a column name and value.

    Parameters:
    gdf (GeoDataFrame): The GeoDataFrame to search.
    column_name (str): The column name to match.
    value (str or int or float): The value to match in the specified column.

    Returns:
    GeoDataFrame: A GeoDataFrame containing the matched row.
    """
    # Check if column exists in the GeoDataFrame
    if column_name not in gdf.columns:
        raise ValueError(f"Column '{column_name}' does not exist in the GeoDataFrame.")

    # Filter the GeoDataFrame based on the column and value
    filtered_gdf = gdf[gdf[column_name] == value]

    if bus_isochrone:
        filtered_gdf = filtered_gdf[filtered_gdf['value'] == 900]

    # Return the filtered GeoDataFrame
    return filtered_gdf.to_crs(epsg=4326)


def get_poi_data_for_bus_isochrone(isochrones: gpd.GeoDataFrame, matching_column: str | int | float, matching_column_value: str, time: str = "2021-01-01") -> gpd.GeoDataFrame:
    if time is None:
        time = datetime.now().strftime("%Y-%m-%d")
    poly_gdf = get_row_by_column(isochrones, matching_column, matching_column_value, True)
    client = OhsomeClient()
    return query_ohsome_api_count(client, poly_gdf, time, "amenity=*")


def get_poi_data_for_walk_isochrone(isochrones: gpd.GeoDataFrame, matching_column: list, matching_column_value: list, time: str = "2021-01-01") -> gpd.GeoDataFrame:
    if len(matching_column) != 2 or len(matching_column_value) != 2:
        raise ValueError("Matching column and value must be a list of two elements.")
    if time is None:
        time = datetime.now().strftime("%Y-%m-%d")
    poly_gdf = get_row_by_column(isochrones, matching_column[0], matching_column_value[0], False)
    poly_gdf = get_row_by_column(poly_gdf, matching_column[1], matching_column_value[1], False)
    client = OhsomeClient()
    return query_ohsome_api_count(client, poly_gdf, time, "amenity=*")


def load_config_from_file() -> dict:
    """Load configuration from file on disk."""
    path = "config.yml"
    if os.path.isfile(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)
    else:
        return {}


def get_config_value(key: str) -> str | int | dict:
    config = load_config_from_file()
    return config[key]