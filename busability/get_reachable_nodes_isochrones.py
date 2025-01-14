import logging
from datetime import datetime, timedelta
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

from busability.network_preprocessing.network_creator import (
    get_union_reachable_polygons,
)
from busability.network_preprocessing.network_creator import load_graph_from_file
from busability.network_processing.network_analyzer import get_multimodal_poi_directness
from busability.utils import get_config_value

iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path"))

iso_polygons_gdf = iso_polygons_gdf.to_crs(get_config_value("crs"))

mode = get_config_value("mode")
start_time_string = get_config_value("date")
minute_threshold = get_config_value("minute_threshold")
matching_column = get_config_value("matching_column")
output_path = get_config_value("output_path")
city_name = get_config_value("city_name")

iso_polygons_gdf["matching"] = (
    iso_polygons_gdf[matching_column].astype(str)
    + "_"
    + (iso_polygons_gdf["value"] / 60).astype(str)
)

start_time_object = datetime.combine(
    datetime.today(), datetime.strptime(start_time_string, "%H:%M:%S").time()
)
end_time_object = start_time_object + timedelta(minutes=minute_threshold)

bus_graph = load_graph_from_file(f"{output_path}{city_name}_bus_graph.gml")
walk_graph = load_graph_from_file(f"{output_path}{city_name}_walk_graph.gml")
bus_graph = load_graph_from_file(f"{output_path}{city_name}_bus_graph.gml")

logging.log(logging.INFO, "Loaded graphs from file")

# Get start and target nodes
target_nodes = [node for node in bus_graph.nodes]
start_nodes = [item for item in walk_graph.nodes if item not in target_nodes]


def process_start_node(start_node):
    """Function to process a single start node."""
    all_reachable_nodes = get_multimodal_poi_directness(
        walk_graph,
        bus_graph,
        walk_graph,
        start_node,
        target_nodes,
        start_time=start_time_object,
        weight_threshold=minute_threshold,
        mode=mode,
    )
    union_gdf = get_union_reachable_polygons(
        iso_polygons_gdf,
        matching_column=matching_column,
        polygon_names=all_reachable_nodes,
        crs=get_config_value("crs"),
        start_node=start_node,
    )
    return union_gdf


if __name__ == "__main__":
    # Use multiprocessing to process start nodes in parallel
    with Pool(processes=cpu_count() - 1) as pool:  # Use all but one CPU core
        result_gdf_list = list(
            tqdm(
                pool.imap(process_start_node, start_nodes),
                total=len(start_nodes),
                desc="Calculating reachable nodes",
            )
        )

    final_gdf = gpd.GeoDataFrame(pd.concat(result_gdf_list, ignore_index=True))

    final_gdf.to_file(
        f"{output_path}{city_name}_union_polygon.geojson", driver="GeoJSON"
    )
