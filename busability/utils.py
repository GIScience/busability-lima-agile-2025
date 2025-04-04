import os

import yaml


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
    if column_name not in gdf.columns:
        raise ValueError(f"Column '{column_name}' does not exist in the GeoDataFrame.")

    filtered_gdf = gdf[gdf[column_name] == value]

    if bus_isochrone:
        filtered_gdf = filtered_gdf[filtered_gdf["value"] == 900]

    return filtered_gdf.to_crs(epsg=4326)


def load_config_from_file(path: str) -> dict:
    """Load configuration from file on disk."""
    if os.path.isfile(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)
    else:
        return {}


def get_config_value(key: str, path: str = "../config/config.yml") -> str | int | dict:
    config = load_config_from_file(path)
    return config[key]
