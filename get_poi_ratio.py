import pandas as pd
import geopandas as gpd
from tqdm import tqdm
import logging
from multiprocessing import Pool
from network_preprocessing.network_creator import get_drive_isochrone, get_poi_inside_isochrone
from network_processing.network_analyzer import get_intersected_isochrones, get_multimodal_isos
from utils import get_config_value

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def process_row(row):
    index = row.name
    try:
        start_node = hexagons_centroids_gdf.loc[index, get_config_value("matching_column")]

        start_centroid = hexagons_centroids_gdf.loc[index, 'geometry']

        start_centroid = gpd.GeoDataFrame(geometry=[start_centroid], crs=hexagons_centroids_gdf.crs)

        drive_iso_for_start_node = get_drive_isochrone(drive_iso_gdf, start_node, matching_column=get_config_value("matching_column"))

        pois_count_drive = get_poi_inside_isochrone(pois_gdf, drive_iso_for_start_node)

        walk_iso_from_start_centroid = walk_isochrones_from_hex[walk_isochrones_from_hex[get_config_value("matching_column")] == start_node]

        walk_isos_for_start_node = get_intersected_isochrones(iso_polygons_gdf, start_centroid)

        calc_isos_for_start_node = get_multimodal_isos(calc_isochrones_gdf, walk_isos_for_start_node)

        bus_merged_gdf = gpd.GeoDataFrame(pd.concat([walk_iso_from_start_centroid, calc_isos_for_start_node], ignore_index=True))

        bus_unioned_geometry = bus_merged_gdf.union_all()

        bus_unioned_gdf = gpd.GeoDataFrame(geometry=[bus_unioned_geometry], crs=bus_merged_gdf.crs)

        pois_count_bus = get_poi_inside_isochrone(pois_gdf, bus_unioned_gdf)

        if pois_count_drive != 0:
            poi_ratio = pois_count_bus / pois_count_drive
        else:
            poi_ratio = 0
        return index, poi_ratio, pois_count_bus, pois_count_drive, bus_unioned_gdf

    except Exception as e:
        logger.error(f"Failed to process row {index}: {e}")
        return index, None, None, None, None

try:
    logger.info("Loading input files...")
    drive_iso_gdf = gpd.read_file(get_config_value("drive_iso_gdf_path"))
    pois_gdf = gpd.read_file(get_config_value("pois_gdf_path"))
    iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path"))
    hexagon_gdf = gpd.read_file(get_config_value("hexagon_gdf_path"))
    hexagons_centroids_gdf = gpd.read_file(get_config_value("hexagon_centroid_gdf_path"))
    calc_isochrones_gdf = gpd.read_file(get_config_value("computed_iso_polygons_gdf_path"))
    walk_isochrones_from_hex = gpd.read_file(get_config_value("walk_isochrones_from_hex_gdf_path"))
except Exception as e:
    logger.critical(f"Failed to read input files: {e}")
    raise RuntimeError(f"Failed to read input files: {e}")

try:
    logger.info("Converting CRS...")
    crs = get_config_value("crs")
    drive_iso_gdf = drive_iso_gdf.to_crs(crs)
    pois_gdf = pois_gdf.to_crs(crs)
    iso_polygons_gdf = iso_polygons_gdf.to_crs(crs)
    hexagon_gdf = hexagon_gdf.to_crs(crs)
    hexagons_centroids_gdf = hexagons_centroids_gdf.to_crs(crs)
    calc_isochrones_gdf = calc_isochrones_gdf.to_crs(crs)
    walk_isochrones_from_start_nodes = walk_isochrones_from_hex.to_crs(crs)
except Exception as e:
    logger.critical(f"Failed to convert CRS: {e}")
    raise RuntimeError(f"Failed to convert CRS: {e}")

try:
    logger.info("Processing data with multiprocessing...")
    with Pool() as pool:
        results = list(tqdm(pool.imap(process_row, [row for _, row in hexagons_centroids_gdf.iterrows()]), total=len(hexagons_centroids_gdf)))
    gdf_list = []
    for index, poi_ratio, pois_count_bus, pois_count_drive, bus_gdf in results:
        gdf_list.append(bus_gdf)
        hexagons_centroids_gdf.loc[index, 'poi_ratio'] = poi_ratio
        hexagons_centroids_gdf.loc[index, 'pois_count_bus'] = pois_count_bus
        hexagons_centroids_gdf.loc[index, 'pois_count_drive'] = pois_count_drive

except Exception as e:
    logger.critical(f"Failed during processing: {e}")
    raise RuntimeError(f"Failed during processing: {e}")

try:
    output_path = get_config_value("output_path")
    city_name = get_config_value("city_name")
    logger.info(f"Saving output to {output_path}{city_name}_poi_ratio_for_reachable_nodes.geojson")
    hexagons_centroids_gdf.to_file(f"{output_path}{city_name}_poi_ratio_for_reachable_nodes.geojson", driver="GeoJSON")
    bus_isos_gdf = pd.concat(gdf_list, ignore_index=True)
    bus_isos_gdf.to_file(f'{output_path}_bus_combined.geojson', driver='GeoJSON')
except Exception as e:
    logger.critical(f"Failed to save output file: {e}")
    raise RuntimeError(f"Failed to save output file: {e}")

logger.info("Processing complete.")
