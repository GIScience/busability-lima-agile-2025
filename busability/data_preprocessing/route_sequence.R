# Check if required packages are installed
required_packages <- c("tidyverse", "tools")
new_packages <- required_packages[!(required_packages %in% installed.packages()[, "Package"])]

# Install missing packages
if (length(new_packages) > 0) {
  install.packages(new_packages, dependencies = TRUE)
}

# Load the libraries
lapply(required_packages, library, character.only = TRUE)

# Define paths 
city_name <- "lima"  # Change to desired study area
base_data_dir <- "../../data"  #folder, where the gtfs folder is stored
gtfs_directory <- file.path(base_data_dir, city_name, "<gtfs-folder-name>")  # name of the GTFS folder
output_directory <- base_data_dir  # Output directory path, can be the same as the folder, where the GTFS folder is

create_route_sequences <- function(gtfs_dir, output_dir) {
  
  # Define file paths
  routes_file <- file.path(gtfs_dir, "routes.txt")
  trips_file <- file.path(gtfs_dir, "trips.txt")
  stop_times_file <- file.path(gtfs_dir, "stop_times.txt")
  stops_file <- file.path(gtfs_dir, "stops.txt")
  
  required_files <- c(routes_file, trips_file, stop_times_file, stops_file)
  missing_files <- required_files[!file.exists(required_files)]
  
  if (length(missing_files) > 0) {
    stop("Missing required GTFS files: ", paste(basename(missing_files), collapse = ", "))
  }
  cat("Reading GTFS files...\n")
  routes <- read.csv(routes_file, stringsAsFactors = FALSE)
  trips <- read.csv(trips_file, stringsAsFactors = FALSE)
  stop_times <- read.csv(stop_times_file, stringsAsFactors = FALSE)
  stops <- read.csv(stops_file, stringsAsFactors = FALSE)
  cat("Processing route stop sequences...\n")
  
  trips_with_stop_count <- trips %>%
    left_join(stop_times %>% 
                group_by(trip_id) %>% 
                summarize(stop_count = n()), 
              by = "trip_id") %>%
    group_by(route_id) %>%
    arrange(desc(stop_count)) %>%
    slice(1) %>%
    select(route_id, trip_id)
  
  # Join all the data to get the final result
  route_stops <- trips_with_stop_count %>%
    left_join(stop_times %>% select(trip_id, stop_id, stop_sequence), by = "trip_id") %>%
    left_join(stops %>% select(stop_id, stop_lon, stop_lat, stop_name), by = "stop_id") %>%
    arrange(route_id, stop_sequence) %>%
    select(route_id, stop_id, stop_sequence, stop_lon, stop_lat, stop_name)
  
  # Write the output to CSV
  output_name <- paste(city_name, "_stops_seq.csv")
  output_file <- file.path(output_dir, output_name)
  cat("Writing output to", output_file, "...\n")
  
  # Create output directory if it doesn't exist
  if (!dir.exists(dirname(output_file))) {
    dir.create(dirname(output_file), recursive = TRUE)
    cat("Created output directory:", dirname(output_file), "\n")
  }
  
  write.csv(route_stops, output_file, row.names = FALSE, quote = TRUE)
  
  cat("Done! Output saved to", output_file, "\n")
  return(output_file)
}

# Example usage
# Call the function to process the data
if (file.exists(gtfs_directory)) {
  result <- create_route_sequences(gtfs_directory, output_directory)
} else {
  cat("Please set 'gtfs_directory' to the folder containing your GTFS files\n")
}

