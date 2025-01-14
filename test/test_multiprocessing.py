import pytest
import time
import geopandas as gpd
import pandas as pd
from multiprocessing import Pool, cpu_count
from datetime import datetime, timedelta
from network_processing.network_analyzer import (
    get_config_value, get_multimodal_poi_directness,
)
from network_preprocessing.network_creator import load_graph_from_file, get_union_reachable_polygons, \
    create_network_from_gtfs
from get_reachable_nodes_isochrones import process_start_node, walk_graph


# Load GeoDataFrames and set configurations
@pytest.fixture(scope="module")
def setup_data():
    drive_iso_gdf = gpd.read_file(get_config_value("drive_iso_gdf_path"))
    pois_gdf = gpd.read_file(get_config_value("pois_gdf_path"))
    iso_polygons_gdf = gpd.read_file(get_config_value("iso_polygons_gdf_path"))
    hexagons_centroids_gdf = gpd.read_file(get_config_value("hexagon_centroid_gdf_path"))

    crs = get_config_value("crs")
    drive_iso_gdf = drive_iso_gdf.to_crs(crs)
    pois_gdf = pois_gdf.to_crs(crs)
    iso_polygons_gdf = iso_polygons_gdf.to_crs(crs)
    hexagons_centroids_gdf = hexagons_centroids_gdf.to_crs(crs)

    start_time_string = get_config_value("date")
    minute_threshold = get_config_value("minute_threshold")
    start_time_object = datetime.combine(datetime.today(), datetime.strptime(start_time_string, "%H:%M:%S").time())

    start_time = datetime.combine(datetime.today(), time(8, 0))
    end_time = start_time + timedelta(minutes=20)
    bus_graph = create_network_from_gtfs("london", base_path=".", start_time=start_time,
                                           end_time=start_time + timedelta(minutes=20))
    walk_graph = bus_graph
    target_nodes = [node for node in bus_graph.nodes]
    start_nodes = [item for item in walk_graph.nodes if item not in target_nodes]

    return {
        'drive_iso_gdf': drive_iso_gdf,
        'pois_gdf': pois_gdf,
        'iso_polygons_gdf': iso_polygons_gdf,
        'hexagons_centroids_gdf': hexagons_centroids_gdf,
        'start_time_object': start_time_object,
        'minute_threshold': minute_threshold,
        'walk_graph': walk_graph,
        'bus_graph': bus_graph,
        'target_nodes': target_nodes,
        'start_nodes': start_nodes,
        'mode': get_config_value("mode"),
        'matching_column': get_config_value("matching_column")
    }


# Single-threaded test
def test_single_threaded_execution(setup_data):
    result_gdf_list = []

    start_time = time.time()
    for start_node in setup_data['start_nodes']:
        all_reachable_nodes = get_multimodal_poi_directness(
            setup_data['walk_graph'], setup_data['bus_graph'], setup_data['walk_graph'],
            start_node, setup_data['target_nodes'], start_time=setup_data['start_time_object'],
            weight_threshold=setup_data['minute_threshold'], mode=setup_data['mode']
        )

        union_gdf = get_union_reachable_polygons(
            setup_data['iso_polygons_gdf'], matching_column=setup_data['matching_column'],
            polygon_names=all_reachable_nodes, crs=setup_data['drive_iso_gdf'].crs, start_node=start_node
        )
        result_gdf_list.append(union_gdf)

    end_time = time.time()
    print(f"Single-threaded execution time: {end_time - start_time:.2f} seconds")

    assert len(result_gdf_list) > 0, "No results were generated in single-threaded execution"
    return result_gdf_list


# Multiprocessing test
def test_multiprocessing_execution(setup_data):
    start_time = time.time()

    with Pool(processes=cpu_count() - 1) as pool:
        result_gdf_list = list(pool.imap(process_start_node, setup_data['start_nodes']))

    end_time = time.time()
    print(f"Multiprocessing execution time: {end_time - start_time:.2f} seconds")

    assert len(result_gdf_list) > 0, "No results were generated in multiprocessing execution"
    return result_gdf_list


# Compare single-threaded and multiprocessing results
def test_compare_results(setup_data):
    # Get results from single-threaded execution
    single_thread_result_gdf_list = test_single_threaded_execution(setup_data)

    # Get results from multiprocessing execution
    multiprocessing_result_gdf_list = test_multiprocessing_execution(setup_data)

    single_thread_result_gdf = gpd.GeoDataFrame(pd.concat(single_thread_result_gdf_list, ignore_index=True))
    multiprocessing_result_gdf = gpd.GeoDataFrame(pd.concat(multiprocessing_result_gdf_list, ignore_index=True))

    # Check if the GeoDataFrames are identical
    assert single_thread_result_gdf.equals(
        multiprocessing_result_gdf), "Results differ between single-threaded and multiprocessing executions"
