from datetime import datetime

import geopandas as gpd
import networkx as nx
import pandas as pd

from busability.network_preprocessing.network_creator import get_union_reachable_polygons, get_drive_isochrone, get_poi_inside_isochrone
from network_processing.network_analyzer import get_multimodal_poi_directness
from utils import get_config_value

drive_iso_gdf = gpd.read_file(get_config_value("drive_iso_gdf_path"))
pois_gdf = gpd.read_file(get_config_value("pois_gdf_path"))
iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path"))

drive_iso_gdf = drive_iso_gdf.to_crs(get_config_value("crs"))
pois_gdf = pois_gdf.to_crs(get_config_value("crs"))
iso_polygons_gdf = iso_polygons_gdf.to_crs(get_config_value("crs"))

walk_graph = nx.read_graphml(get_config_value("output_path") + get_config_value("city_name") + "_walk_graph.graphml")

bus_graph = nx.read_graphml(get_config_value("output_path") + get_config_value("city_name") + "_bus_graph.graphml")

target_nodes = [node for node in bus_graph.nodes]

result_gdf_list = []

for start_node in walk_graph.nodes:

    all_reachable_nodes = get_multimodal_poi_directness(walk_graph, bus_graph, walk_graph, start_node, target_nodes, start_time=minute_threshold, weight_threshold=date_object)

    union_gdf = get_union_reachable_polygons(iso_polygons_gdf, matching_column=get_config_value("matching_column"), polygon_names=all_reachable_nodes, crs=32718)

    drive_iso_for_start_node = get_drive_isochrone(drive_iso_gdf, start_node, matching_column=get_config_value("matching_column"))

    pois_count_drive = get_poi_inside_isochrone(pois_gdf, drive_iso_for_start_node)

    pois_count_bus = get_poi_inside_isochrone(pois_gdf, union_gdf)

    if pois_count_drive != 0:
        poi_ratio = pois_count_bus / pois_count_drive
    else:
        # TODO: do we want to return something else if there are no POIs?
        poi_ratio = 0

    union_gdf["poi_ratio"] = poi_ratio

    print(pois_count_bus)
    print(pois_count_drive)
    print(poi_ratio)

    result_gdf_list.append(union_gdf)

final_gdf = gpd.GeoDataFrame(pd.concat(result_gdf_list, ignore_index=True))

final_gdf.to_file(get_config_value("output_path") + get_config_value("city_name") + "_union_polygon.geojson", driver='GeoJSON')
