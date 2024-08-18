import networkx as nx


def shortest_paths_to_nodes(graph, start, nodes):
    '''Get the shortest paths to the nodes from the start node.'''
    return {node: nx.shortest_path_length(graph, start, node, weight='weight')
            for node in nodes if nx.has_path(graph, start, node)}


def reachable_nodes_via_bus_network(bus_graph, node, remaining_weight):
    '''Get all reachable nodes via the bus network remaining weight.'''
    paths = nx.single_source_dijkstra(bus_graph, node, weight='weight', cutoff=remaining_weight)
    return {key: remaining_weight - value for key, value in paths[0].items()}


def reachable_nodes_to_pois(bus_graph, nodes_dict, remaining_weight):
    '''Get all reachable nodes from the bus network to the POIs within the remaining weight.'''
    all_nodes = set()
    for node, rem_weight in nodes_dict.items():
        paths = nx.single_source_dijkstra(bus_graph, node, weight='weight', cutoff=rem_weight)
        all_nodes.update(paths[0].keys())
    return all_nodes

def get_multimodal_poi_directness(to_bus_stop_graph, bus_stop_graph, from_bus_stop_graph, start_node, target_nodes,
                                  weight_threshold):


    shortest_paths = shortest_paths_to_nodes(to_bus_stop_graph, start_node, target_nodes)

    if not shortest_paths:
        print("No path found to any node in the list from the start node.")
        return 0

    # Step 2: Find the nearest node in the target nodes
    nearest_node = min(shortest_paths, key=shortest_paths.get)
    shortest_distance = shortest_paths[nearest_node]

    if shortest_distance > weight_threshold:
        print("No path found to any node in the list from the start node.")
        return 0

    print(f"Nearest node in list: {nearest_node}, Shortest distance: {shortest_distance}")

    # Step 3: Find all reachable nodes from the nearest bus stop node within the remaining weight
    remaining_weight = weight_threshold - shortest_distance
    reachable_nodes_dict = reachable_nodes_via_bus_network(bus_stop_graph, nearest_node, remaining_weight)

    # Step 4: Find all reachable nodes from the bus stop nodes to POIs
    all_reachable_nodes = reachable_nodes_to_pois(from_bus_stop_graph, reachable_nodes_dict, remaining_weight)

    print(f"All reachable nodes: {all_reachable_nodes}")

    # Step 5: Calculate the number of POIs reachable from the start node
    # node_attributes = nx.get_node_attributes(from_bus_stop_graph, 'poi')
    # poi_count = sum(node_attributes.get(node, 0) for node in all_reachable_nodes)

    return all_reachable_nodes