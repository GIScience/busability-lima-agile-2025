from datetime import timedelta

import networkx as nx


def shortest_paths_to_nodes(graph, start, nodes):
    '''Get the shortest paths to the nodes from the start node.'''
    return {node: nx.shortest_path_length(graph, start, node, weight='weight')
            for node in nodes if nx.has_path(graph, start, node)}


def reachable_nodes_via_bus_network(bus_graph, node, remaining_weight, current_time, end_time):
    '''Get all reachable nodes via the bus network remaining weight.'''
    paths = nx.single_source_dijkstra(bus_graph, node, weight='weight', cutoff=remaining_weight)
    return time_dependent_reachable_nodes_via_bus_network(node, bus_graph, current_time, end_time)


def time_dependent_reachable_nodes_via_bus_network(start_node, graph, start_time, end_time):
    def dfs(node, current_time):
        if current_time > end_time:
            return set()

        reachable = {node: current_time}
        try:
            for neighbor in graph[node]:
                edge_data = graph.get_edge_data(node, neighbor)
                if "is_transfer" in edge_data.keys():
                    reachable.update(dfs(neighbor, current_time + timedelta(minutes=int(edge_data["weight"]))))
                elif edge_data["arrival_time"] <= end_time:
                    reachable.update(dfs(neighbor, edge_data["arrival_time"]))
        except Exception as err:
            raise err


        return reachable

    return dfs(start_node, start_time)



def reachable_nodes_to_pois(bus_graph, nodes_dict, end_time):
    '''Get all reachable nodes from the bus network to the POIs within the remaining weight.'''
    all_nodes = set()
    for node, current_time in nodes_dict.items():
        remaining_time = (end_time - current_time).total_seconds() / 60
        paths = nx.single_source_dijkstra(bus_graph, node, weight='weight', cutoff=remaining_time)
        all_nodes.update(paths[0].keys())
    return all_nodes

def get_multimodal_poi_directness(to_bus_stop_graph, bus_stop_graph, from_bus_stop_graph, start_node, target_nodes, start_time,
                                  weight_threshold):

    reachable_nodes = set()
    shortest_paths = shortest_paths_to_nodes(to_bus_stop_graph, start_node, target_nodes)

    if not shortest_paths:
        print("No path found to any node in the list from the start node.")
        return 0
    end_time = start_time + timedelta(minutes=weight_threshold)
    # Step 2: Find the nearest node in the target nodes
    for node, path_length in shortest_paths.items():



        if path_length > weight_threshold:
            continue

        # Step 3: Find all reachable nodes from the nearest bus stop node within the remaining weight
        current_time = start_time + timedelta(minutes=path_length)
        remaining_time = weight_threshold - path_length

        reachable_nodes_dict = reachable_nodes_via_bus_network(bus_stop_graph, node, remaining_time, current_time, end_time)

        # Step 4: Find all reachable nodes from the bus stop nodes to POIs
        all_reachable_nodes = reachable_nodes_to_pois(from_bus_stop_graph, reachable_nodes_dict, end_time)

        reachable_nodes.update(all_reachable_nodes)
        # Step 5: Calculate the number of POIs reachable from the start node
        # node_attributes = nx.get_node_attributes(from_bus_stop_graph, 'poi')
        # poi_count = sum(node_attributes.get(node, 0) for node in all_reachable_nodes)

    return reachable_nodes