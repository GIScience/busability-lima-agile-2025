import copy
from datetime import timedelta, datetime

import networkx as nx
import geopandas as gpd

from utils import get_config_value


def shortest_paths_to_nodes(graph, start, nodes):
    '''Get the shortest paths to the nodes from the start node.'''
    return {node: nx.shortest_path_length(graph, start, node, weight='weight')
            for node in nodes if nx.has_path(graph, start, node)}

def get_bus_station_from_isochrone(node):
    bus_station_node, distance= node.split('_')
    return (bus_station_node, int(float(distance)))


def reachable_nodes_via_bus_network(bus_graph, node, remaining_weight, current_time, end_time, mode):
    '''Get all reachable nodes via the bus network remaining weight.'''
    #paths = nx.single_source_dijkstra(bus_graph, node, weight='weight', cutoff=remaining_weight)
    return time_dependent_reachable_nodes_via_bus_network(node, bus_graph, current_time, end_time, mode)


def time_dependent_reachable_nodes_via_bus_network(start_node, graph, start_time, end_time, mode="normal"):
    visited = set()
    reachable = {}

    def dfs(node, current_time, trip_id=None):
        if current_time > end_time:
            return

        # Mark the current node as reachable at the current time
        reachable[node] = current_time
        visited.add(node)

        if mode == "normal":
            try:
                for neighbor in graph[node]:
                    edge_data = graph.get_edge_data(node, neighbor)

                    if "is_transfer" in edge_data.keys():
                        # Handle transfer edges, only proceed if neighbor hasn't been visited in the current path
                        if neighbor not in visited:
                            dfs(neighbor, current_time + timedelta(minutes=int(edge_data["weight"])))
                    else:
                        # Handle time-dependent edges
                        for time_entry in edge_data['times']:
                            if isinstance(time_entry['arrival_time'], str):
                                time_entry['arrival_time'] = datetime.strptime(time_entry['arrival_time'], '%Y-%m-%d %H:%M:%S')
                            if isinstance(time_entry['departure_time'], str):
                                time_entry['departure_time'] = datetime.strptime(time_entry['departure_time'], '%Y-%m-%d %H:%M:%S')

                        next_time_info = None

                        # Find the next valid departure time after the current time
                        for time_info in edge_data['times']:
                            if time_info['departure_time'] >= current_time:
                                next_time_info = time_info
                                if next_time_info['arrival_time'] <= end_time:
                                    dfs(neighbor, next_time_info['arrival_time'])
                                    #TODO: break?

            except Exception as err:
                raise err

        elif mode == "rush_hour":
            try:
                for neighbor in graph[node]:
                    edge_data = graph.get_edge_data(node, neighbor)

                    if "is_transfer" in edge_data.keys():
                        # Handle transfer edges, only proceed if neighbor hasn't been visited in the current path
                        if neighbor not in visited:
                            dfs(neighbor, current_time + timedelta(minutes=int(edge_data["weight"])))
                    else:
                        # Handle time-dependent edges
                        for time_entry in edge_data['times']:
                            if isinstance(time_entry['arrival_time'], str):
                                time_entry['arrival_time'] = datetime.strptime(time_entry['arrival_time'], '%Y-%m-%d %H:%M:%S')
                            if isinstance(time_entry['departure_time'], str):
                                time_entry['departure_time'] = datetime.strptime(time_entry['departure_time'], '%Y-%m-%d %H:%M:%S')

                        next_time_info = None
                        next_trip_id = None

                        # Find the next valid departure time after the current time
                        for time_info in edge_data['times']:

                            time_info_copy = copy.deepcopy(time_info)

                            if time_info_copy.get('trip_id') == trip_id:
                                duration = (edge_data['len_two_lanes'] + edge_data["len_more_than_two_lanes"]) / (
                                            get_config_value("rush_hour_speed") / 3.6) / 60
                                time_info_copy['arrival_time'] = current_time + timedelta(minutes=duration)
                                next_time_info = time_info_copy
                                next_trip_id = time_info_copy.get('trip_id')
                                break
                            if time_info_copy['departure_time'] >= current_time:
                                duration = (edge_data['len_two_lanes'] + edge_data["len_more_than_two_lanes"]) / (
                                            get_config_value("rush_hour_speed") / 3.6) / 60
                                time_info_copy['arrival_time'] = current_time + timedelta(minutes=duration)
                                next_time_info = time_info_copy
                                next_trip_id = time_info_copy.get('trip_id')
                                break

                        # If a valid next time was found, and it's within the allowed time window
                        if next_time_info and next_time_info['arrival_time'] <= end_time:
                            dfs(neighbor, next_time_info['arrival_time'], trip_id=next_trip_id)
            except Exception as err:
                raise err

        elif mode == "rush_hour_priority_lane":
            bus_speed = get_config_value("bus_speed")

            try:
                for neighbor in graph[node]:
                    edge_data = graph.get_edge_data(node, neighbor)

                    if "is_transfer" in edge_data.keys():
                        # Handle transfer edges, only proceed if neighbor hasn't been visited in the current path
                        if neighbor not in visited:
                            dfs(neighbor, current_time + timedelta(minutes=int(edge_data["weight"])))
                    else:
                        # Handle time-dependent edges
                        for time_entry in edge_data['times']:
                            if isinstance(time_entry['arrival_time'], str):
                                time_entry['arrival_time'] = datetime.strptime(time_entry['arrival_time'],
                                                                               '%Y-%m-%d %H:%M:%S')
                            if isinstance(time_entry['departure_time'], str):
                                time_entry['departure_time'] = datetime.strptime(time_entry['departure_time'],
                                                                                 '%Y-%m-%d %H:%M:%S')

                        next_time_info = None
                        next_trip_id = None

                        # Find the next valid departure time after the current time
                        for time_info in edge_data['times']:

                            time_info_copy = copy.deepcopy(time_info)

                            if time_info_copy.get('trip_id') == trip_id:
                                duration = ((edge_data['len_two_lanes'] / (get_config_value("rush_hour_speed") / 3.6)) + (edge_data["len_more_than_two_lanes"] / (
                                        bus_speed / 3.6))) / 60
                                time_info_copy['arrival_time'] = current_time + timedelta(minutes=duration)
                                next_time_info = time_info_copy
                                next_trip_id = time_info_copy.get('trip_id')
                                break
                            if time_info_copy['departure_time'] >= current_time:
                                duration = ((edge_data['len_two_lanes'] / (get_config_value("rush_hour_speed") / 3.6)) + (
                                            bus_speed / (
                                            get_config_value("rush_hour_speed") / 3.6))) / 60
                                time_info_copy['arrival_time'] = current_time + timedelta(minutes=duration)
                                next_time_info = time_info_copy
                                next_trip_id = time_info_copy.get('trip_id')
                                break

                        # If a valid next time was found, and it's within the allowed time window
                        if next_time_info and next_time_info['arrival_time'] <= end_time:
                            dfs(neighbor, next_time_info['arrival_time'], trip_id=next_trip_id)

            except Exception as err:
                raise err

        else:
            raise ValueError("Invalid mode. Please choose either 'normal', 'rush_hour' or 'rush_hour_priority_lane' mode.")

    # Start the DFS with the visited and reachable sets as shared variables
    dfs(start_node, start_time)
    return reachable




def reachable_nodes_to_pois(bus_graph, nodes_dict, end_time):
    '''Get all reachable nodes from the bus network to the POIs within the remaining weight.'''
    all_nodes = set()
    for node, current_time in nodes_dict.items():
        if node not in bus_graph:
            continue
        remaining_time = (end_time - current_time).total_seconds() / 60
        paths = nx.single_source_dijkstra(bus_graph, node, weight='weight', cutoff=remaining_time)
        all_nodes.update(paths[0].keys())
    return all_nodes

def get_multimodal_poi_directness(to_bus_stop_graph, bus_stop_graph, from_bus_stop_graph, start_node, target_nodes, start_time,
                                  weight_threshold, mode):

    reachable_nodes = set()

    bus_node, path_length = get_bus_station_from_isochrone(start_node)

    end_time = start_time + timedelta(minutes=weight_threshold)

    if path_length > weight_threshold:
        return set()

    # Step 3: Find all reachable nodes from the nearest bus stop node within the remaining weight
    current_time = start_time + timedelta(minutes=path_length)
    remaining_time = weight_threshold - path_length

    reachable_nodes_dict = reachable_nodes_via_bus_network(bus_stop_graph, bus_node, remaining_time, current_time, end_time, mode=mode)
    reachable_nodes.update(reachable_nodes_dict.keys())
    # Step 4: Find all reachable nodes from the bus stop nodes to POIs
    all_reachable_nodes = reachable_nodes_to_pois(from_bus_stop_graph, reachable_nodes_dict, end_time)

    reachable_nodes.update(all_reachable_nodes)
    # Step 5: Calculate the number of POIs reachable from the start node
    # node_attributes = nx.get_node_attributes(from_bus_stop_graph, 'poi')
    # poi_count = sum(node_attributes.get(node, 0) for node in all_reachable_nodes)

    return reachable_nodes


def get_nodes_of_intersected_isochrones(isochrones_gdf, hexagon_gdf, matching_column):
    ''' Get the nodes of the intersected isochrones'''
    intersections = gpd.sjoin(isochrones_gdf, hexagon_gdf, how='inner', op='intersects')

    node_names = set(intersections[matching_column])

    return node_names


def get_centroids(gdf):
    ''' Get the centroids of the GeoDataFrame'''
    centroids = gdf.geometry.centroid

    centroid_gdf = gpd.GeoDataFrame(gdf.drop(columns='geometry'), geometry=centroids, crs=gdf.crs)

    return centroid_gdf


def get_intersected_isochrones(isochrones_gdf, hexagon_centroid_gdf):
    ''' Get the intersected isochrones'''
    intersections = gpd.sjoin(isochrones_gdf, hexagon_centroid_gdf, how='inner', op='intersects')

    return intersections
