from datetime import datetime, timedelta

import geopandas as gpd

import logging

from busability.network_preprocessing.network_creator import (
    get_graphs,
    save_graph_to_file,
)
from busability.utils import get_config_value

config_path = "../config/config_create_graphs.yml"

matching_column = get_config_value("matching_column", config_path)

minute_threshold = get_config_value("minute_threshold",config_path)

output_path = get_config_value("output_path", config_path)

city = get_config_value("city_name", config_path)

iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path", config_path))

iso_polygons_gdf = iso_polygons_gdf.to_crs(get_config_value("crs", config_path))

start_time_string = get_config_value("date", config_path)

start_time_object = datetime.strptime(start_time_string, "%H:%M:%S").time()

logging.log(logging.INFO, "Creating graphs for " + city)

end_time_object = datetime.combine(datetime.today(), start_time_object) + timedelta(
    minutes=minute_threshold
)

bus_graph, walk_graph = get_graphs(
    city, start_time_object, end_time_object, iso_polygons_gdf, matching_column
)

save_graph_to_file(bus_graph, output_path + city + "_bus_graph.gml")
save_graph_to_file(walk_graph, output_path + city + "_walk_graph.gml")
