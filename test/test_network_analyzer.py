from network_processing.network_analyzer import get_multimodal_poi_directness, shortest_paths_to_nodes, \
    reachable_nodes_via_bus_network, reachable_nodes_to_pois
from busability.network_preprocessing.network_creator import create_network_from_gtfs


def test_shortest_paths_to_nodes(walk_to_busstop_network):
    start_node = 1
    target_nodes = [4, 5]
    result = shortest_paths_to_nodes(walk_to_busstop_network, start_node, target_nodes)
    assert result == {4: 3, 5: 6}

def test_reachable_nodes_via_bus_network(bus_network):
    node = 4
    remaining_weight = 10
    result = reachable_nodes_via_bus_network(bus_network, node, remaining_weight)
    assert result == {4: 10, 6: 3, 7: 7, 8: 2}

def test_reachable_nodes_to_pois(walk_from_bus_stop):
    nodes_dict = {7: 10, 6: 3}
    remaining_weight = 10
    result = reachable_nodes_to_pois(walk_from_bus_stop, nodes_dict, remaining_weight)
    assert result == {7, 15, 10, 16, 11, 6}

def test_get_multimodal_poi_directness(walk_to_busstop_network, bus_network, walk_from_bus_stop):
    start_node = 1
    target_nodes = [4, 5]
    weight_threshold = 10
    result = get_multimodal_poi_directness(walk_to_busstop_network, bus_network, walk_from_bus_stop, start_node, target_nodes, weight_threshold)
    assert result == {12, 6, 4, 10, 7, 13}


def test_gtfs_network_analysis(walk_to_busstop_network, walk_from_bus_stop):
    bus_network = create_network_from_gtfs("london", base_path=".")
    start_node = 1
    target_nodes = [4, 5]
    weight_threshold = 10
    result = get_multimodal_poi_directness(walk_to_busstop_network, bus_network, walk_from_bus_stop, start_node,
                                           target_nodes, weight_threshold)
    assert result == {4, 6, 7, 9, 10, 12, 13, 15, 16}