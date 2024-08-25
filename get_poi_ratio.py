from network_preprocessing.network_creator import get_drive_isochrone, get_poi_inside_isochrone
from network_processing.network_analyzer import get_intersected_isochrones
from utils import get_config_value

import geopandas as gpd

drive_iso_gdf = gpd.read_file(get_config_value("drive_iso_gdf_path"))
pois_gdf = gpd.read_file(get_config_value("pois_gdf_path"))
iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path"))
hexagons_centroids_gdf = gpd.read_file(get_config_value("hexagon_centroid_gdf_path"))

drive_iso_gdf = drive_iso_gdf.to_crs(get_config_value("crs"))
pois_gdf = pois_gdf.to_crs(get_config_value("crs"))
iso_polygons_gdf = iso_polygons_gdf.to_crs(get_config_value("crs"))
hexagons_centroids_gdf = hexagons_centroids_gdf.to_crs(get_config_value("crs"))

for index, row in hexagons_centroids_gdf.iterrows():

    start_node = row[get_config_value("matching_column")]
    drive_iso_for_start_node = get_drive_isochrone(drive_iso_gdf, start_node, matching_column=get_config_value("matching_column"))

    pois_count_drive = get_poi_inside_isochrone(pois_gdf, drive_iso_for_start_node)

    bus_isochrone = get_intersected_isochrones(iso_polygons_gdf, hexagons_centroids_gdf)

    pois_count_bus = get_poi_inside_isochrone(pois_gdf, bus_isochrone)

    if pois_count_drive != 0:
        poi_ratio = pois_count_bus / pois_count_drive
    else:
        # TODO: do we want to return something else if there are no POIs?
        poi_ratio = 0

    # add poi_ratio to the hexagons_centroids_gdf
    hexagons_centroids_gdf.loc[index, 'poi_ratio'] = poi_ratio

output_path = get_config_value("output_path")
hexagons_centroids_gdf.to_file(output_path + "poi_ratio_for_reachable_nodes.geojson", driver="GeoJSON")