from datetime import datetime, time, timedelta
from unittest.mock import patch

from network_processing.network_analyzer import get_multimodal_poi_directness, shortest_paths_to_nodes, \
    reachable_nodes_via_bus_network, reachable_nodes_to_pois, get_nodes_of_intersected_isochrones, get_centroids, \
    time_dependent_reachable_nodes_via_bus_network, get_bus_station_from_isochrone
from busability.network_preprocessing.network_creator import create_network_from_gtfs


def test_shortest_paths_to_nodes(walk_to_busstop_network):
    start_node = 1
    target_nodes = [4, 5]
    result = shortest_paths_to_nodes(walk_to_busstop_network, start_node, target_nodes)
    assert result == {4: 3, 5: 6}

@patch('network_processing.network_analyzer.get_bus_station_from_isochrone', return_value=(4,1))
def test_gtfs_network_analysis(walk_to_busstop_network, walk_from_bus_stop, start_time):
    start_node = 1
    target_nodes = [4, 5]
    weight_threshold = 10
    bus_network = create_network_from_gtfs("london", base_path=".", start_time=start_time, end_time=start_time + timedelta(minutes=weight_threshold))

    result = get_multimodal_poi_directness(walk_to_busstop_network, bus_network, walk_from_bus_stop, start_node,
                                           target_nodes, weight_threshold=weight_threshold, start_time=start_time)
    assert result == {4, 6, 7, 8, 10, 12, 13, 15, 16}


def test_get_nodes_of_intersected_isochrones(bus_isochrones_gdf, hexagons_gdf):
    matching_column = "NUEVO_CODIGO"
    result = get_nodes_of_intersected_isochrones(bus_isochrones_gdf, hexagons_gdf, matching_column)
    assert result == {2072.0, 2074.0}


def test_get_centroids(hexagons_gdf):
    result = get_centroids(hexagons_gdf)
    assert set(hexagons_gdf.columns) == set(result.columns)
    assert all(result.geom_type == 'Point')


def test_time_dependent_reachable_nodes_via_bus_network_rush_hour(start_time):
    start_node = 4
    weight_threshold = 20
    end_time = start_time + timedelta(minutes=weight_threshold)
    bus_network = create_network_from_gtfs("london", base_path=".", start_time=start_time,
                                           end_time=start_time + timedelta(minutes=weight_threshold))
    result = time_dependent_reachable_nodes_via_bus_network(start_node, bus_network, start_time, end_time, mode="rush_hour")
    assert result.keys() == {4, 6, 9, 10, 8}
    result_normal = time_dependent_reachable_nodes_via_bus_network(start_node, bus_network, start_time, end_time,
                                                            mode="normal")
    assert result.keys() != result_normal.keys()

def test_time_dependent_reachable_nodes_via_bus_network_rush_hour_priority_lane(start_time):
    start_node = 4
    weight_threshold = 20
    end_time = start_time + timedelta(minutes=weight_threshold)
    bus_network = create_network_from_gtfs("london", base_path=".", start_time=start_time,
                                           end_time=start_time + timedelta(minutes=weight_threshold))
    result = time_dependent_reachable_nodes_via_bus_network(start_node, bus_network, start_time, end_time, mode="rush_hour_priority_lane")
    result_rush_hour = time_dependent_reachable_nodes_via_bus_network(start_node, bus_network, start_time, end_time, mode="rush_hour")
    assert result.keys() == {4, 6, 7, 9, 10, 8}
    result_normal = time_dependent_reachable_nodes_via_bus_network(start_node, bus_network, start_time, end_time,
                                                            mode="normal")
    assert result.keys() != result_normal.keys()
    assert result.keys() != result_rush_hour.keys()


def test_get_bus_station_from_isochrone():
    isochrone_node = "test_1.0"
    result = get_bus_station_from_isochrone(isochrone_node)
    assert result == ('test', 1)
