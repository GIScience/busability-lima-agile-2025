import pandas as pd
import geopandas as gpd

from get_hexagons import hexagon
from network_preprocessing.network_creator import get_drive_isochrone, get_poi_inside_isochrone
from network_processing.network_analyzer import get_intersected_isochrones
from utils import get_config_value

try:
    drive_iso_gdf = gpd.read_file(get_config_value("drive_iso_gdf_path"))
    pois_gdf = gpd.read_file(get_config_value("pois_gdf_path"))
    iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path"))
    hexagon_gdf = gpd.read_file(get_config_value("hexagon_gdf_path"))
    hexagons_centroids_gdf = gpd.read_file(get_config_value("hexagon_centroid_gdf_path"))
    walk_isochrones_from_hex = gpd.read_file(get_config_value("walk_isochrones_from_hex_gdf_path"))
except Exception as e:
    raise RuntimeError(f"Failed to read input files: {e}")

try:
    drive_iso_gdf = drive_iso_gdf.to_crs(get_config_value("crs"))
    pois_gdf = pois_gdf.to_crs(get_config_value("crs"))
    iso_polygons_gdf = iso_polygons_gdf.to_crs(get_config_value("crs"))
    hexagon_gdf = hexagon_gdf.to_crs(get_config_value("crs"))
    hexagons_centroids_gdf = hexagons_centroids_gdf.to_crs(get_config_value("crs"))
    walk_isochrones_from_start_nodes = walk_isochrones_from_hex.to_crs(get_config_value("crs"))
except Exception as e:
    raise RuntimeError(f"Failed to convert CRS: {e}")

for index, row in hexagons_centroids_gdf.iterrows():
    try:
        start_node = row[get_config_value("matching_column")]
        drive_iso_for_start_node = get_drive_isochrone(drive_iso_gdf, start_node, matching_column=get_config_value("matching_column"))

        pois_count_drive = get_poi_inside_isochrone(pois_gdf, drive_iso_for_start_node)

        walk_iso_for_start_node = get_intersected_isochrones(walk_isochrones_from_start_nodes, hexagons_centroids_gdf)

        bus_isochrone = get_intersected_isochrones(iso_polygons_gdf, hexagons_centroids_gdf)

        bus_merged_gdf = gpd.GeoDataFrame(pd.concat([walk_iso_for_start_node, bus_isochrone], ignore_index=True))

        bus_unioned_geometry = bus_merged_gdf.unary_union

        bus_unioned_gdf = gpd.GeoDataFrame(geometry=[bus_unioned_geometry], crs=bus_merged_gdf.crs)

        pois_count_bus = get_poi_inside_isochrone(pois_gdf, bus_unioned_gdf)

        if pois_count_drive != 0:
            poi_ratio = pois_count_bus / pois_count_drive
        else:
            poi_ratio = 0

        hexagons_centroids_gdf.loc[index, 'poi_ratio'] = poi_ratio

    except Exception as e:
        print(f"Failed to process row {index} with start_node {start_node}: {e}")
        hexagons_centroids_gdf.loc[index, 'poi_ratio'] = None

try:
    output_path = get_config_value("output_path")
    hexagons_centroids_gdf.to_file(output_path + get_config_value("city_name") + "_poi_ratio_for_reachable_nodes.geojson", driver="GeoJSON")
except Exception as e:
    raise RuntimeError(f"Failed to save output file: {e}")