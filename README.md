> **⚠️ Warning**: This repository is currently under construction. Some features may be incomplete or not functioning. Data is not yet included. Repository will be ready for the reproducibility review.



This repository includes the code and instructions for the paper `Towards Green Cities: Analysis of the Impact of Bus-Priority Lanes and Accessibility Indicators on Emission Control for Highly Congested Metropolitan Areas During Peak Times` for the for the 28th AGILE conference, Geographic Information Science responding to Global Challenges.

## Installing Dependencies with Poetry

To set up the project and install all dependencies specified in the `pyproject.toml` file, use the following command:

```bash
poetry install
```

Activate the environment:

```bash
poetry shell
```

## Data Preprocessing

To create the lanes.txt files that are required in Network Creation, the .ipynb files must first be executed in the data_preprocessing directory. First, the bus routes need to be clipped to get the geometry of the path between
two stops in a sequence with [get_route_geometry_between_stops.ipynb](busability/data_preprocessing/get_route_geometry_between_stops.ipynb). After that, the routes need to be connected with OSM data in order to create the lanes.txt files,
that are needed for the network creation. Run the script in [get_lanes_info.ipynb](busability/data_preprocessing/get_lanes_info.ipynb), rename the resulting file to a .txt file and add it in the respective GTFS directory.



