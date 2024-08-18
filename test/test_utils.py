from ohsome import OhsomeClient
from shapely import Geometry

from utils import query_ohsome_api_count, get_road_data, load_config_from_file, \
    get_config_value


def test_query_ohsome_api_count(heidelberg_gdf):
    client = OhsomeClient()
    time = "2021-01-01"

    result = query_ohsome_api_count(client, heidelberg_gdf, time, "amenity=*")
    assert result is not None
    assert isinstance(result, float)

def test_query_ohsome_api_extract(heidelberg_gdf):
    client = OhsomeClient()
    time = "2021-01-01"
    result = get_road_data(client, heidelberg_gdf, time)
    assert result is not None
    assert len(result) > 0
    assert isinstance(result.iloc[0]["geometry"], Geometry)
    assert isinstance(result.iloc[0]["@other_tags"], dict)


def test_load_config_from_file():
    result = load_config_from_file()
    assert result is not None
    assert isinstance(result, dict)


# def test_get_config_value():
#     result = get_config_value("city_name")
#     assert result is not None
#     assert isinstance(result, str)



