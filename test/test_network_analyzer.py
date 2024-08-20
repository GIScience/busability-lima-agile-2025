from datetime import datetime, time, timedelta

from network_processing.network_analyzer import get_multimodal_poi_directness, shortest_paths_to_nodes, \
    reachable_nodes_via_bus_network, reachable_nodes_to_pois
from busability.network_preprocessing.network_creator import create_network_from_gtfs


def test_shortest_paths_to_nodes(walk_to_busstop_network):
    start_node = 1
    target_nodes = [4, 5]
    result = shortest_paths_to_nodes(walk_to_busstop_network, start_node, target_nodes)
    assert result == {4: 3, 5: 6}


def test_gtfs_network_analysis(walk_to_busstop_network, walk_from_bus_stop, start_time):
    start_node = 1
    target_nodes = [4, 5]
    weight_threshold = 10
    bus_network = create_network_from_gtfs("london", base_path=".", start_time=start_time, end_time=start_time + timedelta(minutes=weight_threshold))

    result = get_multimodal_poi_directness(walk_to_busstop_network, bus_network, walk_from_bus_stop, start_node,
                                           target_nodes, weight_threshold=weight_threshold, start_time=start_time)
    assert result == {4, 5, 6, 7, 10, 12, 13, 15, 16}