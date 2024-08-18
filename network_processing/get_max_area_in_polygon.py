import geopandas as gpd
import pandas as pd


def process_polygons(single_polygons, multiple_polygons):

    multiple_polygons = multiple_polygons.to_crs(single_polygons.crs)

    result_gdf_list = []
    results_hexagon_list = []

    for _, single_polygon in single_polygons.iterrows():
        single_polygon_gdf = gpd.GeoDataFrame([single_polygon], crs=single_polygons.crs)

        clipped_polygons = gpd.overlay(multiple_polygons, single_polygon_gdf, how='intersection')
        if clipped_polygons.empty:
            continue

        remaining_polygons = clipped_polygons.sort_values(by='poi_ratio', ascending=False)

        remaining_polygon = single_polygon_gdf
        remaining_polygons_list = []

        for _, polygon in remaining_polygons.iterrows():
            polygon_gdf = gpd.GeoDataFrame([polygon], crs=single_polygons.crs)

            intersection = gpd.overlay(remaining_polygon, polygon_gdf, how='intersection')
            remaining_polygon = gpd.overlay(remaining_polygon, intersection, how='difference')

            if intersection.empty:
                continue

            intersection = intersection.to_crs(32718)
            intersection['poi_ratio'] = polygon['poi_ratio']
            if intersection.geom_type.isin(['Polygon', 'MultiPolygon']).all():
                remaining_polygons_list.append(intersection)

        if not remaining_polygons_list:
            continue

        remaining_polygons_gdf = gpd.GeoDataFrame(pd.concat(remaining_polygons_list, ignore_index=True))
        remaining_polygons_gdf = remaining_polygons_gdf.to_crs(32718)
        single_polygon_gdf = single_polygon_gdf.to_crs(32718)

        area_hex = single_polygon_gdf.geometry.area.values[0]
        remaining_polygons_gdf["area"] = remaining_polygons_gdf.geometry.area

        poi_values = []
        not_covered_area_ratio = 0
        for _, row in remaining_polygons_gdf.iterrows():
            poi_value = row['poi_ratio'] * (row['area'] / area_hex)
            poi_values.append(poi_value)
            not_covered_area_ratio += (row['area'] / area_hex)

        remaining_polygons_gdf['poi_value'] = poi_values
        poi_value = sum(poi_values) + (1 - not_covered_area_ratio * 0)

        result_gdf_list.append(remaining_polygons_gdf)
        single_polygon_gdf['poi_value'] = poi_value
        results_hexagon_list.append(single_polygon_gdf)

    final_gdf = gpd.GeoDataFrame(pd.concat(result_gdf_list, ignore_index=True))


    final_hex_gdf = gpd.GeoDataFrame(pd.concat(results_hexagon_list, ignore_index=True))

    return final_gdf, final_hex_gdf
