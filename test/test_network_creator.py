from datetime import timedelta

import networkx as nx
from shapely import Point

from busability.network_preprocessing.network_creator import calculate_distance, gdf_to_nodes_and_weighted_edges, \
    create_walk_edges, get_union_reachable_polygons, get_drive_isochrone, get_poi_inside_isochrone, \
    create_network_from_gtfs, peartree_graph, gtfs2nx_graph


def test_calculate_distance(point1, point2):
    assert calculate_distance(point1, point2) == 1


def test_calculate_distance(point1):
    assert calculate_distance(point1, point1) == 0


def test_gdf_to_nodes_and_weighted_edges(bus_stop_gdf, bus_isochrones_gdf):
    nodes, edges = gdf_to_nodes_and_weighted_edges(bus_stop_gdf, bus_isochrones_gdf, 'NUEVO_CODIGO')

    assert len(nodes) == 2
    assert len(edges) == 1
    for node in nodes:
        assert 'name' in node[1]
        assert 'point' in node[1]
        assert 'poi' in node[1]
        assert isinstance(node[1]['poi'], float)
        assert isinstance(node[1]['point'], Point)
    assert isinstance(edges[0][2], float)
    assert edges[0][1] == nodes[1][0]
    assert edges[0][0] == nodes[0][0]


def test_gdf_to_nodes_and_weighted_edges(bus_stop_gdf, bus_isochrones_gdf):
    nodes, edges = create_walk_edges(bus_stop_gdf, bus_isochrones_gdf, 'NUEVO_CODIGO')
    assert len(nodes) == 2
    assert len(edges) == 2
    for node in nodes:
        assert 'name' in node[1]
    for edge in edges:
        assert isinstance(edge[2], float)
        assert edge[0] not in [nodes[0][0], nodes[1][0]]
        assert edge[1] in [nodes[0][0], nodes[1][0]]
        assert edge[0] != edge[1]

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
