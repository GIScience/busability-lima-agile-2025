import logging
import os
from datetime import datetime
from typing import List

import geopandas as gpd
import networkx as nx
import pandas as pd
from tqdm import tqdm


def calculate_distance(point1, point2):
    return point1.distance(point2) / 100


# Function to convert GeoDataFrame to nodes with attributes and create edges with weights
def gdf_to_nodes_and_weighted_edges(gdf, matching_name):
    ''' Create nodes and edges from a GeoDataFrame from each bus stop'''
    nodes = []
    edges = []

    for idx, row in gdf.iterrows():
        point = row['geometry']
        name = row.get(matching_name)
        #node = (name, {'name': name, 'point': point, "poi": get_poi_data_for_bus_isochrone(isochrones_gdf, matching_name, row[matching_name])})
        node = (name, {'name': name, 'point': point})
        nodes.append(node)

        # Add edge to the next node with weight if it exists
        if idx < len(gdf) - 1:
            next_row = gdf.iloc[idx + 1]
            next_name = next_row.get(matching_name)
            next_point = next_row['geometry']
            weight = calculate_distance(point, next_point)
            edges.append((name, next_name, weight))

    return nodes, edges


def create_walk_edges(bus_graph, isochrones_gdf, matching_name):
    ''' Create nodes and edges from a GeoDataFrame for each isochrone'''

    logging.log(logging.INFO, "Creating walk graph...")
    walk_graph = bus_graph.copy()

    walk_graph.clear_edges()

    # Iterate over each row in the isochrones_gdf
    for idx, row in isochrones_gdf.iterrows():
        name = row.get(matching_name)
        value = row.get('value') / 60

        # The name for the new node
        new_node_name = f"{name}_{value}"

        # Create the new node with attributes
        node_attributes = {'name': new_node_name}

        # Add the new node to the graph if it doesn't exist
        if not walk_graph.has_node(new_node_name):
            walk_graph.add_node(new_node_name, **node_attributes)

        # Add the edge between the existing node and the new node
        walk_graph.add_edge(name, new_node_name, weight=int(value))
        walk_graph.add_edge(new_node_name, name, weight=int(value))

    # Return the new graph
    return walk_graph

def get_union_reachable_polygons(gdf, matching_column: str, polygon_names: List[str], start_node: str, crs: int = 32718):
    ''' Get the union of the polygons that are reachable from the nodes in the graph'''

    if not polygon_names or all('_' not in item for item in polygon_names):
        return None
    # union the polygons
    union = gdf[gdf["matching"].isin(polygon_names)].unary_union

    union_gdf = gpd.GeoDataFrame(geometry=[union])

    union_gdf = union_gdf.set_crs(epsg=crs)

    union_gdf[matching_column] = start_node

    return union_gdf


def get_drive_isochrone(drive_isochrones_gdf, start_node, matching_column: str):
    spatial_index = drive_isochrones_gdf.sindex

    possible_matches_index = list(spatial_index.intersection(
        drive_isochrones_gdf[drive_isochrones_gdf[matching_column] == start_node].geometry.bounds.values[0]
    ))

    possible_matches = drive_isochrones_gdf.iloc[possible_matches_index]

    precise_match = possible_matches[possible_matches[matching_column] == start_node]

    return precise_match

def get_poi_inside_isochrone(pois_gdf, isochrone_gdf):
    columns_to_drop = [col for col in ["index_right", "index_left"] if col in isochrone_gdf.columns]
    if columns_to_drop:
        isochrone_gdf = isochrone_gdf.drop(columns=columns_to_drop)

    joined_gdf = gpd.sjoin(pois_gdf, isochrone_gdf, how="inner", predicate="within")

    return len(joined_gdf)


def create_network_from_gtfs(city, start_time, end_time, base_path=None):
    """
    Load GTFS data for the specified city.

    Args:
    - city (str): The city for which to load GTFS data.
    - base_path (str, optional): The base path to the data directory. If None, defaults to the directory of this script.

    Returns:
    - A graph created from the GTFS data.
    """

    # Use the provided base_path or the directory of this script
    if base_path is None:
        path = os.path.join( "data", city.lower(), "gtfs")
    else:
        path = os.path.join(base_path, "data", city.lower(), "gtfs")

    if not os.path.exists(path):
        raise FileNotFoundError(f"The GTFS directory for '{city}' does not exist.")

    stops = pd.read_csv(os.path.join(path, 'stops.txt'))
    stop_times = pd.read_csv(os.path.join(path, 'stop_times.txt'))

    if os.path.exists(os.path.join(path, 'transfers.txt')):
        transfers = pd.read_csv(os.path.join(path, 'transfers.txt'))
    else:
        transfers = pd.DataFrame()
        logging.log(logging.INFO, "No transfers.txt file found. No transfer edges will be added to the graph.")

    if os.path.exists(os.path.join(path, 'lanes.txt')):
        lanes = pd.read_csv(os.path.join(path, 'lanes.txt'))
    else:
        lanes = pd.DataFrame()
        logging.log(logging.INFO, "No lanes.txt file found. No lane attributes will be added to the graph.")


    logging.log(logging.INFO, "Loaded GTFS files. Creating graph...")

    return create_gtfs_graph(stops, stop_times, transfers, lanes, start_time, end_time)



def create_gtfs_graph(stops, stop_times, transfers, lanes, start_time, end_time):

    # Convert arrival and departure times in stop_times to datetime.time objects
    def convert_to_time(value):
        try:
            return pd.to_datetime(value, format='%H:%M:%S').time()
        except ValueError:
            return None

    # Convert start_time and end_time to datetime.time objects
    start_time = pd.to_datetime(start_time, format='%H:%M:%S').time()
    end_time = pd.to_datetime(end_time, format='%H:%M:%S').time()

    # Assuming stop_times is your DataFrame
    stop_times['arrival_time'] = stop_times['arrival_time'].apply(convert_to_time)
    stop_times['departure_time'] = stop_times['departure_time'].apply(convert_to_time)

    logging.log(logging.INFO, "Converted times.")

    # Filter stop_times DataFrame to keep only rows within the time range
    stop_times = stop_times[
        (stop_times['arrival_time'] >= start_time) & (stop_times['arrival_time'] <= end_time) &
        (stop_times['departure_time'] >= start_time) & (stop_times['departure_time'] <= end_time)
        ]

    # Create a directed graph
    G = nx.DiGraph()

    # Add nodes based on stops with a progress bar
    for _, stop in tqdm(stops.iterrows(), total=stops.shape[0], desc="Adding nodes"):
        G.add_node(str(stop['stop_id']), name=stop['stop_name'], lat=stop['stop_lat'], lon=stop['stop_lon'])

    # Add edges based on stop_times with time-dependent weights with a progress bar
    for _, stop_time in tqdm(stop_times.iterrows(), total=stop_times.shape[0], desc="Adding edges"):
        # Skip rows with None in departure_time or arrival_time
        if stop_time['departure_time'] is None or stop_time['arrival_time'] is None:
            continue

        # Check if the departure time is within the specified time range
        if start_time <= stop_time['departure_time'] <= end_time:
            # Find the next stop in the trip sequence
            next_stop_time = stop_times[(stop_times['trip_id'] == stop_time['trip_id']) &
                                        (stop_times['stop_sequence'] == stop_time['stop_sequence'] + 1)]

            if not next_stop_time.empty:
                next_stop_time = next_stop_time.iloc[0]

                # Skip rows with None in next_stop_time's times
                if next_stop_time['departure_time'] is None or next_stop_time['arrival_time'] is None:
                    continue

                # Calculate travel time in minutes
                departure_time_full = datetime.combine(datetime.today(), stop_time['departure_time'])
                arrival_time_full = datetime.combine(datetime.today(), next_stop_time['arrival_time'])
                travel_time = arrival_time_full - departure_time_full
                travel_time_minutes = travel_time.total_seconds() / 60

                # Create an edge with a list of times and trip_id if it doesn't exist yet
                if G.has_edge(str(stop_time['stop_id']), str(next_stop_time['stop_id'])):
                    G[str(stop_time['stop_id'])][str(next_stop_time['stop_id'])]['times'].append({
                        'departure_time': departure_time_full.strftime("%Y-%m-%d %H:%M:%S"),
                        'arrival_time': arrival_time_full.strftime("%Y-%m-%d %H:%M:%S"),
                        'travel_time_minutes': travel_time_minutes,
                        'trip_id': stop_time['trip_id']
                    })
                else:
                    G.add_edge(str(stop_time['stop_id']), str(next_stop_time['stop_id']), times=[{
                        'departure_time': departure_time_full.strftime("%Y-%m-%d %H:%M:%S"),
                        'arrival_time': arrival_time_full.strftime("%Y-%m-%d %H:%M:%S"),
                        'travel_time_minutes': travel_time_minutes,
                        'trip_id': stop_time['trip_id']
                    }])

    # Add transfer edges from the transfers.txt file with a progress bar
    for _, transfer in tqdm(transfers.iterrows(), total=transfers.shape[0], desc="Adding transfer edges"):
        from_stop_id = transfer['from_stop_id']
        to_stop_id = transfer['to_stop_id']
        min_transfer_time = transfer['min_transfer_time'] / 60

        # Add the transfer edge with the minimum transfer time as the weight
        G.add_edge(str(from_stop_id), str(to_stop_id), weight=int(min_transfer_time), is_transfer=True)

    # Add lane attributes to the edges
    for _, lane in tqdm(lanes.iterrows(), total=lanes.shape[0], desc="Adding lane attributes"):
        try:
            from_stop_id = str(int(lane['start_id']))
            to_stop_id = str(int(lane['end_id']))
        except ValueError:
            from_stop_id = str(lane['start_id'])
            to_stop_id = str(lane['end_id'])

        if not G.has_edge(from_stop_id, to_stop_id):
            continue

        len_two_lanes = lane['len_two_lanes'] if lane['len_two_lanes'] is not None else 0
        len_more_than_two_lanes = lane['len_more_than_two_lanes'] if lane['len_more_than_two_lanes'] is not None else 0

        G[from_stop_id][to_stop_id]['len_two_lanes'] = str(len_two_lanes)
        G[from_stop_id][to_stop_id]['len_more_than_two_lanes'] = str(len_more_than_two_lanes)

    logging.log(logging.INFO, "GTFS graph created.")

    return G



def save_graph_to_file(graph, filename):
     # Assuming G is your graph

    logging.log(logging.INFO, "Saving graph to file: " + filename)
    nx.write_gml(graph, filename)


def get_graphs(city, start_time_object, end_time_object, iso_polygons_gdf, matching_column, path_to_gtfs=None):
    bus_graph = create_network_from_gtfs(city, start_time_object, end_time_object, base_path=path_to_gtfs)

    walk_graph = create_walk_edges(bus_graph, iso_polygons_gdf, matching_name=matching_column)

    return bus_graph, walk_graph


def load_graph_from_file(filename):
    return nx.read_gml(filename)
