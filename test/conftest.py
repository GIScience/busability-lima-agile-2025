import os
from datetime import datetime, time

import networkx as nx
import pytest
import geopandas as gpd
from shapely import Point

@pytest.fixture
def data_dir(monkeypatch):
    data_dir = os.path.abspath('busability/data')

    monkeypatch.setenv('DATA_DIR', data_dir)


@pytest.fixture
def heidelberg_gdf():
    return gpd.read_file("data/feature-collection-heidelberg-bahnstadt-bergheim-weststadt.geojson")

@pytest.fixture
def bus_stop_gdf():
    return gpd.read_file("data/test_bus_stops.geojson").to_crs(epsg=4326)

@pytest.fixture
def bus_isochrones_gdf():
    return gpd.read_file("data/test_bus_isochrones.geojson").to_crs(epsg=4326)

@pytest.fixture
def drive_isos_gdf():
    return gpd.read_file("data/drive_isos_test.gpkg").to_crs(epsg=4326)


@pytest.fixture
def pois_gdf():
    return gpd.read_file("data/pois_test.gpkg").to_crs(epsg=4326)


@pytest.fixture
def result_union_isos_gdf():
    return gpd.read_file("data/union_polygon.geojson").to_crs(epsg=4326)


@pytest.fixture
def hexagons_gdf():
    return gpd.read_file("data/hexagons.geojson").to_crs(epsg=4326)


@pytest.fixture
def point1():
    return Point(0, 0)

@pytest.fixture
def point2():
    return Point(0, 100)

@pytest.fixture
def start_time():
    return datetime.combine(datetime.today(), time(8, 0))

@pytest.fixture
def gdf():
    gdf = gpd.GeoDataFrame(geometry=[Point(0, 0), Point(0, 1), Point(0, 2)])
    gdf['APROXIMACION'] = ['A', 'B', 'C']
    return gdf

@pytest.fixture
def walk_to_busstop_network():
    G = nx.Graph()

    nodes_with_attributes = [
        ("1", {'name': 'Node A', 'point': Point(0, 0)}),
        ("2", {'name': 'Node B', 'point': Point(1, 1)}),
        ("3", {'name': 'Node C', 'point': Point(2, 2)}),
        ("4", {'name': 'Node D', 'point': Point(3, 3)}),
        ("5", {'name': 'Node E', 'point': Point(4, 4)})
    ]

    G.add_nodes_from(nodes_with_attributes)

    edges_with_weights = [
        ("1", "2", 2),
        ("1", "3", 5),
        ("2", "3", 1),
        ("2", "4", 1),
        ("3", "4", 2),
        ("4", "5", 3),
    ]

    G.add_weighted_edges_from(edges_with_weights)

    return G

@pytest.fixture
def bus_network():
    G = nx.Graph()

    nodes_with_attributes = [
        ("4", {'name': 'Node D', 'point': Point(0, 0)}),
        ("5", {'name': 'Node X', 'point': Point(0, 0)}),
        ("6", {'name': 'Node F', 'point': Point(1, 1)}),
        ("7", {'name': 'Node G', 'point': Point(2, 2)}),
        ("8", {'name': 'Node H', 'point': Point(3, 3)}),
        ("9", {'name': 'Node J', 'point': Point(4, 4)})
    ]

    G.add_nodes_from(nodes_with_attributes)

    edges_with_weights = [
        ("4", "6", 7),
        ("4", "7", 3),
        ("6", "7", 5),
        ("7", "8", 5),
        ("8", "9", 4)
    ]

    G.add_weighted_edges_from(edges_with_weights)

    return G

@pytest.fixture
def walk_from_bus_stop():
    G = nx.Graph()

    nodes_with_attributes = [
        ("7", {'name': 'Node G', 'point': Point(2, 2), 'poi': '1'}),
        ("10", {'name': 'Node W', 'point': Point(3, 4), 'poi': '2'}),
        ("11", {'name': 'Node X', 'point': Point(4, 5), 'poi': '3'}),
        ("4", {'name': 'Node D', 'point': Point(4, 3), 'poi': '4'}),
        ("12", {'name': 'Node L', 'point': Point(5, 4), 'poi': '5'}),
        ("13", {'name': 'Node Q', 'point': Point(2, 1), 'poi': '6'}),
        ("6", {'name': 'Node F', 'point': Point(1, 1), 'poi': '7'}),
        ("15", {'name': 'Node M', 'point': Point(1, 2), 'poi': '8'}),
        ("16", {'name': 'Node N', 'point': Point(3, 1), 'poi': '9'}),
        ("9", {'name': 'Node J', 'point': Point(3, 8), 'poi': '9'}),
        ("5", {'name': 'Node X', 'point': Point(3, 8), 'poi': '9'}),
    ]

    G.add_nodes_from(nodes_with_attributes)

    edges_with_weights = [
        ("7", "10", {'weight': 2}),
        ("7", "11", {'weight': 5}),
        ("4", "12", {'weight': 1}),
        ("4", "13", {'weight': 1}),
        ("6", "15", {'weight': 2}),
        ("6", "16", {'weight': 3})
    ]

    G.add_edges_from(edges_with_weights)

    return G
