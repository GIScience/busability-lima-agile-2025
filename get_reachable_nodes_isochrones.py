import logging
from datetime import datetime, timedelta

import geopandas as gpd
import networkx as nx
import pandas as pd
from tqdm import tqdm

from busability.network_preprocessing.network_creator import get_union_reachable_polygons, get_drive_isochrone, get_poi_inside_isochrone
from network_preprocessing.network_creator import load_graph_from_file
from network_processing.network_analyzer import get_multimodal_poi_directness, get_centroids, \
    get_nodes_of_intersected_isochrones
from utils import get_config_value

drive_iso_gdf = gpd.read_file(get_config_value("drive_iso_gdf_path"))
pois_gdf = gpd.read_file(get_config_value("pois_gdf_path"))
iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path"))
hexagons_centroids_gdf = gpd.read_file(get_config_value("hexagon_centroid_gdf_path"))

drive_iso_gdf = drive_iso_gdf.to_crs(get_config_value("crs"))
pois_gdf = pois_gdf.to_crs(get_config_value("crs"))
iso_polygons_gdf = iso_polygons_gdf.to_crs(get_config_value("crs"))
hexagons_centroids_gdf = hexagons_centroids_gdf.to_crs(get_config_value("crs"))

start_time_string = get_config_value("date")

start_time_object = datetime.combine(datetime.today(),datetime.strptime(start_time_string, "%H:%M:%S").time())

minute_threshold = get_config_value("minute_threshold")

end_time_object = start_time_object + timedelta(minutes=minute_threshold)

walk_graph = load_graph_from_file(get_config_value("output_path") + get_config_value("city_name") + "_walk_graph.gml")

bus_graph = load_graph_from_file(get_config_value("output_path") + get_config_value("city_name") + "_bus_graph.gml")

logging.log(logging.INFO, "Loaded graphs from file")

#hexagons_centroids_gdf = get_centroids(iso_polygons_gdf)

#start_nodes = get_nodes_of_intersected_isochrones(iso_polygons_gdf, hexagons_centroids_gdf, get_config_value("matching_column"))
#start_nodes = gpd.read_file(get_config_value("selected_isochrones_path"))

target_nodes = [node for node in bus_graph.nodes]

# remove bus stops from the start nodes
start_nodes = [item for item in walk_graph.nodes if item not in target_nodes]

result_gdf_list = []

#for start_node in tqdm(start_nodes, total=len(start_nodes), desc="Calculating reachable nodes"):
for start_node in tqdm(start_nodes, total=len(start_nodes), desc="Calculating reachable nodes"):

    all_reachable_nodes = get_multimodal_poi_directness(walk_graph, bus_graph, walk_graph, start_node, target_nodes, start_time=start_time_object, weight_threshold=minute_threshold)

    union_gdf = get_union_reachable_polygons(iso_polygons_gdf, matching_column=get_config_value("matching_column"), polygon_names=all_reachable_nodes, crs=get_config_value("crs"))

    result_gdf_list.append(union_gdf)


    final_gdf = gpd.GeoDataFrame(pd.concat(result_gdf_list, ignore_index=True))
    final_gdf.to_file(get_config_value("output_path") + get_config_value("city_name") + "_union_polygon.geojson",
                      driver='GeoJSON')

final_gdf = gpd.GeoDataFrame(pd.concat(result_gdf_list, ignore_index=True))

final_gdf.to_file(get_config_value("output_path") + get_config_value("city_name") + "_union_polygon.geojson", driver='GeoJSON')
