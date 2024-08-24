from datetime import datetime, timedelta

import geopandas as gpd
import networkx as nx

import logging

from network_preprocessing.network_creator import get_graphs, save_graph_to_file
from utils import get_config_value


city = get_config_value("city_name")

logging.log(logging.INFO, "Creating graphs for " + city)

iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path"))

iso_polygons_gdf = iso_polygons_gdf.to_crs(get_config_value("crs"))

logging.log(logging.INFO, "Isochrone polygons loaded")

start_time_string = get_config_value("date")

start_time_object = datetime.strptime(start_time_string, "%H:%M:%S").time()

minute_threshold = get_config_value("minute_threshold")

end_time_object = datetime.combine(datetime.today(), start_time_object) + timedelta(minutes=minute_threshold)

matching_column = get_config_value("matching_column")

bus_graph, walk_graph = get_graphs(city, start_time_object, end_time_object, iso_polygons_gdf, matching_column)

output_path = get_config_value("output_path")

save_graph_to_file(bus_graph, output_path + city + "_bus_graph.graphml")
save_graph_to_file(walk_graph, output_path + city + "_walk_graph.graphml")
