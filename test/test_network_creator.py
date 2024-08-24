from datetime import timedelta

import networkx as nx
from shapely import Point

from busability.network_preprocessing.network_creator import calculate_distance, gdf_to_nodes_and_weighted_edges, \
    create_walk_edges, get_union_reachable_polygons, get_drive_isochrone, get_poi_inside_isochrone, \
    create_network_from_gtfs, get_graphs, save_graph_to_file


def test_calculate_distance(point1, point2):
    assert calculate_distance(point1, point2) == 1


def test_calculate_distance(point1):
    assert calculate_distance(point1, point1) == 0


def test_get_union_reachable_polygons(bus_isochrones_gdf):
    reachable_stops = ['CALLE 25', 'CALLE 37']
    union_gdf = get_union_reachable_polygons(bus_isochrones_gdf, 'APROXIMACION', reachable_stops, crs=32718)
    assert union_gdf is not None
    assert len(union_gdf) == 1
    assert union_gdf.iloc[0]['geometry'].geom_type == 'Polygon'
    assert union_gdf.crs == 32718

def test_get_drive_isochrone(drive_isos_gdf):
    drive_iso = get_drive_isochrone(drive_isos_gdf, 'EL PORTILLO_2.0', 'APROXIMACION')
    assert drive_iso is not None
    assert len(drive_iso) == 1
    assert drive_iso.iloc[0]['geometry'].geom_type == 'Polygon'
    assert drive_iso.iloc[0]['APROXIMACION'] == 'EL PORTILLO_2.0'

def test_get_poi_inside_isochrone(pois_gdf, bus_isochrones_gdf):
    pois = get_poi_inside_isochrone(pois_gdf, bus_isochrones_gdf)
    assert pois is not None
    assert isinstance(pois, int)
    assert pois > 0


def test_create_network_from_gtfs(start_time):
    graph = create_network_from_gtfs("london", base_path=".", start_time=start_time, end_time=start_time + timedelta(minutes=30))
    assert graph is not None
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0
    assert isinstance(graph, nx.Graph)
    shortest_path = nx.shortest_path(graph, source=4, target=9)
    assert shortest_path is not None
    assert isinstance(shortest_path, list)
    edge_data = graph.edges(data=True)
    assert edge_data is not None
    assert isinstance(edge_data._adjdict, dict)
    assert len(edge_data._adjdict) > 0


def test_get_graphs(start_time, bus_isochrones_gdf):
    matching_column = "stop_id"
    end_time = start_time + timedelta(minutes=30)
    bus_graph, walk_graph = get_graphs("london", start_time, end_time, bus_isochrones_gdf, matching_column, path_to_gtfs=".")
    assert bus_graph is not None
    assert walk_graph is not None
    assert len(bus_graph.nodes) < len(walk_graph.nodes)
    assert len(bus_graph.edges) < len(walk_graph.edges)


def test_save_graph_to_file():

    # Create a graph
    G = nx.Graph()

    # Add nodes with list attributes
    G.add_node(1, times=[1, 2, 3])
    G.add_node(2, attribute=['a', 'b', 'c'])
    G.add_edge(1, 2)

    path = "data/test_graph_with_lists.gml"

    save_graph_to_file(G, path)

    G_loaded = nx.read_gml("graph_with_lists.gml")

    assert G.nodes == G_loaded.nodes
    assert G.edges == G_loaded.edges
