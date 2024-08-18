from network_processing.get_max_area_in_polygon import process_polygons


def test_get_max_area_in_polygon(hexagons_gdf, result_union_isos_gdf):
    iso_gdf, hex_gdf = process_polygons(hexagons_gdf, result_union_isos_gdf)
    assert iso_gdf is not None
    assert hex_gdf is not None
    assert "poi_value" in iso_gdf.columns
    assert "poi_value" in hex_gdf.columns