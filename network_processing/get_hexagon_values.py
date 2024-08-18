import geopandas as gpd

from network_processing.get_max_area_in_polygon import process_polygons
from utils import get_config_value

single_polygons = gpd.read_file(get_config_value("hexagon_gdf_path"))
multiple_polygons = gpd.read_file(get_config_value("busability_isochrones_output_path") + get_config_value("city_name") + "_union_polygon.geojson", driver='GeoJSON')


# Run the processing function
final_gdf, final_hex_gdf = process_polygons(single_polygons, multiple_polygons)

final_gdf.to_file(f'../results/{get_config_value("city_name")}_isos_for_poi_density.geojson', driver='GeoJSON')

final_hex_gdf.to_file(f'../results/{get_config_value("city_name")}_hexagons_with_poi_density.geojson', driver='GeoJSON')