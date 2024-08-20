import os
from datetime import datetime
from typing import List

import geopandas as gpd
import networkx as nx
import pandas as pd
import peartree as pt
import gtfs2nx as gx


def calculate_distance(point1, point2):
    return point1.distance(point2) / 100


# Function to convert GeoDataFrame to nodes with attributes and create edges with weights
def gdf_to_nodes_and_weighted_edges(gdf, isochrones_gdf, matching_name):
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


def create_walk_edges(bus_stop_gdf, isochrones_gdf, matching_name):
    ''' Create nodes and edges from a GeoDataFrame for each isochrone'''
    additional_edges = []
    additional_nodes = []

    for idx, row in isochrones_gdf.iterrows():
        name = row.get(matching_name)
        value = row.get('value') / 60

        # Find the matching node in gdf1
        match = bus_stop_gdf[bus_stop_gdf[matching_name] == name]

        if not match.empty:
            point = row['geometry']
            new_node_name = f"{name}_{value}"
            matching_names = [matching_name, 'value']
            matching_values = [name, row["value"]]
            # used for points on surface
            #new_node = (new_node_name, {'name': new_node_name, 'point': point, "poi": np.random.randint(0, 10)})
            #new_node = (new_node_name, {'name': new_node_name, "poi": get_poi_data_for_walk_isochrone(isochrones_gdf, matching_names, matching_values)})
            new_node = (new_node_name, {'name': new_node_name})
            additional_nodes.append(new_node)
            additional_edges.append((name, new_node_name, value))

    return additional_nodes, additional_edges


def get_union_reachable_polygons(gdf, matching_column: str, polygon_names: List[str], crs: int = 32718):
    ''' Get the union of the polygons that are reachable from the nodes in the graph'''

    # union the polygons
    union = gdf[gdf[matching_column].isin(polygon_names)].unary_union

    union_gdf = gpd.GeoDataFrame(geometry=[union])

    union_gdf = union_gdf.set_crs(epsg=crs)

    return union_gdf


def get_drive_isochrone(drive_isochrones_gdf, start_node, matching_column: str):
    return drive_isochrones_gdf[drive_isochrones_gdf[matching_column] == start_node]

def get_poi_inside_isochrone(pois_gdf, isochrone_gdf):

    return len(gpd.sjoin(pois_gdf, isochrone_gdf, how="inner", op="within"))


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
        base_path = os.path.dirname(__file__)

    path = os.path.join(base_path, "data", city.lower(), "gtfs")

    if not os.path.exists(path):
        raise FileNotFoundError(f"The GTFS directory for '{city}' does not exist.")

    stops = pd.read_csv(os.path.join(path, 'stops.txt'))
    stop_times = pd.read_csv(os.path.join(path, 'stop_times.txt'))
    transfers = pd.read_csv(os.path.join(path, 'transfers.txt'))

    return create_gtfs_graph(stops, stop_times, transfers, start_time, end_time)

def create_gtfs_graph(stops, stop_times, transfers, start_time, end_time):
    # Convert start_time and end_time to datetime.time objects
    start_time = pd.to_datetime(start_time, format='%H:%M:%S').time()
    end_time = pd.to_datetime(end_time, format='%H:%M:%S').time()

    # Convert arrival and departure times in stop_times to datetime.time objects
    stop_times['arrival_time'] = pd.to_datetime(stop_times['arrival_time'], format='%H:%M:%S').dt.time
    stop_times['departure_time'] = pd.to_datetime(stop_times['departure_time'], format='%H:%M:%S').dt.time

    # Create a directed graph
    G = nx.DiGraph()

    # Add nodes
    for _, stop in stops.iterrows():
        G.add_node(stop['stop_id'], name=stop['stop_name'], lat=stop['stop_lat'], lon=stop['stop_lon'])

    # Add edges based on stop_times with time-dependent weights
    for _, stop_time in stop_times.iterrows():
        # Check if the departure time is within the specified time range
        if start_time <= stop_time['departure_time'] <= end_time:
            # Find the next stop in the trip sequence
            next_stop_time = stop_times[(stop_times['trip_id'] == stop_time['trip_id']) &
                                        (stop_times['stop_sequence'] == stop_time['stop_sequence'] + 1)]

            if not next_stop_time.empty:
                next_stop_time = next_stop_time.iloc[0]

                # Calculate travel time in minutes
                departure_time_full = datetime.combine(datetime.today(), stop_time['departure_time'])
                arrival_time_full = datetime.combine(datetime.today(), next_stop_time['arrival_time'])
                travel_time = arrival_time_full - departure_time_full
                travel_time_minutes = travel_time.total_seconds() / 60

                # Create an edge with a list of times if it doesn't exist yet
                if G.has_edge(stop_time['stop_id'], next_stop_time['stop_id']):
                    G[stop_time['stop_id']][next_stop_time['stop_id']]['times'].append({
                        'departure_time': stop_time['departure_time'],
                        'arrival_time': next_stop_time['arrival_time'],
                        'travel_time_minutes': travel_time_minutes
                    })
                else:
                    G.add_edge(stop_time['stop_id'], next_stop_time['stop_id'], times=[{
                        'departure_time': stop_time['departure_time'],
                        'arrival_time': next_stop_time['arrival_time'],
                        'travel_time_minutes': travel_time_minutes
                    }])

    # Add transfer edges from the transfers.txt file
    for _, transfer in transfers.iterrows():
        from_stop_id = transfer['from_stop_id']
        to_stop_id = transfer['to_stop_id']
        min_transfer_time = transfer['min_transfer_time']

        # Add the transfer edge with the minimum transfer time as the weight
        G.add_edge(from_stop_id, to_stop_id, weight=min_transfer_time, is_transfer=True)

    return G



def peartree_graph(base_path=None):
    if base_path is None:
        path = os.path.dirname(__file__)
    else:
        path = base_path #'../data/to/itm_london_gtfs.zip'

    # Automatically identify the busiest day and
    # read that in as a Partidge feed
    feed = pt.get_representative_feed(path)

    # Set a target time period to
    # use to summarize impedance
    start = 7*60*60  # 7:00 AM
    end = 8*60*60  # 8:00 AM

    # Converts feed subset into a directed
    # network multigraph
    G = pt.load_feed_as_graph(feed, start, end)


def gtfs2nx_graph(path):
    return gx.transit_graph(path, time_window=('06:00', '06:30'))
