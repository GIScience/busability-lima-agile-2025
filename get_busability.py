import geopandas as gpd
import networkx as nx
import pandas as pd

from busability.network_preprocessing.network_creator import (gdf_to_nodes_and_weighted_edges, create_walk_edges,
                                    get_union_reachable_polygons, get_drive_isochrone, get_poi_inside_isochrone)
from network_processing.network_analyzer import get_multimodal_poi_directness
from utils import get_config_value

bus_gdf = gpd.read_file(get_config_value("bus_gdf_path"))
pois_gdf = gpd.read_file(get_config_value("pois_gdf_path"))
iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path"))
drive_iso_gdf = gpd.read_file(get_config_value("drive_iso_gdf_path"))


bus_gdf = bus_gdf.to_crs(get_config_value("crs"))
pois_gdf = pois_gdf.to_crs(get_config_value("crs"))
iso_polygons_gdf = iso_polygons_gdf.to_crs(get_config_value("crs"))
drive_iso_gdf = drive_iso_gdf.to_crs(get_config_value("crs"))


nodes, edges = gdf_to_nodes_and_weighted_edges(bus_gdf, iso_polygons_gdf, get_config_value("matching_column"))

walk_nodes, walk_edges = create_walk_edges(bus_gdf, iso_polygons_gdf, get_config_value("matching_column"))

G = nx.Graph()

G.add_nodes_from(nodes)

G.add_nodes_from(walk_nodes)

G.add_weighted_edges_from(walk_edges)


G2 = nx.Graph()

G2.add_nodes_from(nodes)

G2.add_weighted_edges_from(edges)

G3 = G

target_nodes = [node for node in G2.nodes]

result_gdf_list = []

for start_node in G3.nodes:

    all_reachable_nodes = get_multimodal_poi_directness(G, G2, G3, start_node, target_nodes, weight_threshold=15)

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

final_gdf.to_file(get_config_value("busability_isochrones_output_path") + get_config_value("city_name") + "_union_polygon.geojson", driver='GeoJSON')
