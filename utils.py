import os
from datetime import datetime

import yaml
import geopandas as gpd


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