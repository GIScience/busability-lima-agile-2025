


This repository includes the code and instructions for the paper `Towards Green Cities: Analysis of the Impact of Bus-Priority Lanes and Accessibility Indicators on Emission Control for Highly Congested Metropolitan Areas During Peak Times` for the for the 28th AGILE conference, Geographic Information Science responding to Global Challenges.

## Requirements

- Python: ≥ 3.10
- Poetry: ≥ 1.5
- R: ≥ 4.0

This project uses [Poetry](https://python-poetry.org/docs/) for packaging and dependencies management. Please make sure it is installed on your system.

## Installing Dependencies with Poetry

To set up the project and install all dependencies specified in the `pyproject.toml` file, use the following command:

```bash
poetry install
```

Activate the environment:

```bash
poetry shell
```

## Get the Data
Download the data for running this workflow for Lima and London [here](https://heibox.uni-heidelberg.de/d/45aede558e8f4282ba10/) and copy the directory as `data` into the repository.

## Docker installation

Please follow the instructions provided here by the official OpenRouteService(ORS) [website](https://giscience.github.io/openrouteservice/run-instance/running-with-docker). We are going to run docker with docker compose (section "Running prebuilt images").

Once you have successfully installed docker and runned docker compose, we will modify the docker compose file to begin with our analysis. 

Look for your docker-compose.yml file and open it. Now you will paste our [modified](busability/data_preprocessing/get_route_geometry_between_stops.ipynb) docker compose file into the docker compose file that you have pulled. 

Depending on which city you want to start with, you need to download the pbf file for [London](https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest.osm.pbf) or [Lima](https://download.geofabrik.de/south-america/peru-latest.osm.pbf). 
Copy the downloaded file into the docker directory and modify the name in line 51 of our docker file. The docker compose file will create the car and walking profiles. This may take some time, but it will be easier to create the isochrones for one country. 
The docker server will be exposed on port 8081. 

Once all is set, run 
```bash
docker compose up -d
```
again. 

## Create GTFS File

First, we need to run the R Markdown [preprocess_files.Rmd](busability-lima-agile-2025/blob/main/make_gtfs/preprocess_files.Rmd). Paste the files "atu_stops.gpkg" and "final_shapes.gpkg" into the make_gtfs_data folder.  
This will create all the required files that we need for the next script.

To create the GTFS File for Lima, we are using the Python package make_gtfs. Since the latest version of the package has some issues, we need to download [this](https://github.com/mrcagney/make_gtfs/releases/tag/4.0.7) version. Download the source code, extract the zip and copy the folder into the make_gtfs_data folder. 
Once you have copied the folder, you can run the [GTFS notebook](busability-lima-agile-2025/blob/main/make_gtfs/make_gtfs_data/make_gtfs.ipynb) that is within make_gtfs_data folder. This notebook will import the make_gtfs package, load the required GTFS data and create a GTFS feed.

## Data Preprocessing

To create the lanes.txt files that are required in Network Creation, the .ipynb files must first be executed in the data_preprocessing directory. First, the bus routes need to be clipped to get the geometry of the path between
two stops in a sequence with [get_route_geometry_between_stops.ipynb](busability/data_preprocessing/get_route_geometry_between_stops.ipynb). After that, the routes need to be connected with OSM data in order to create the lanes.txt files,
that are needed for the network creation. Run the script in [get_lanes_info.ipynb](busability/data_preprocessing/get_lanes_info.ipynb), rename the resulting file to a .txt file and add it in the respective GTFS directory.

## Run Analysis

To run the analysis, you have to first run the following commands. As they take a lot of resources and time, we recommend to use 
a processing server for the calculation, especially for London. To switch between the study areas switch the `config_path`
variable in each file to point to the respective directory (default is `lima`).

```bash
cd busability
python create_graphs.py
```

```bash
python get_reachable_nodes_isochrones.py
```

```bash
python get_poi_ratio.py
```
