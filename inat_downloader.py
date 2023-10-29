import argparse
import csv
import requests
from requests.adapters import HTTPAdapter, Retry
import os
import datetime
import time 

# iNaturalist query limits, minus a safety margin 
MAX_QUERIES_PER_DAY = 9500 # Max allowed : 10000
MAX_MEDIA_PER_HOUR = 4 # Max allowed : 5 GB
MAX_MEDIA_PER_DAY = 22 # Max allowed : 24 GB

# User query information
my_daily_queries = {"value" : 0, "reset_time" : datetime.datetime.now() + datetime.timedelta(hours = 24)}
my_hourly_media = {"value" : 0, "reset_time" : datetime.datetime.now() + datetime.timedelta(hours = 1)}
my_daily_media = {"value" : 0, "reset_time" : datetime.datetime.now() + datetime.timedelta(hours = 24)}

# Run information
max_observations_number = 0 
current_observations_number = 0
current_images_number = 0
current_dataset_size = 0 

# Set up a session that will retry on HTTP errors (429, 500, 502, 503, 504)
session = requests.Session()
retries = Retry(total = 5, backoff_factor = 1, status_forcelist = [429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries = retries))

# Function to comply with iNaturalist query rate limits
def evaluate_query_rate():

    # Evaluate number of queries this day and wait if necessary
    if my_daily_queries["value"] > MAX_QUERIES_PER_DAY:
        while my_daily_queries["reset_time"] > datetime.datetime.now() :
            time_left = my_daily_queries["reset_time"] - datetime.datetime.now()
            print("WARNING : iNaturalist daily queries limit reached, download will resume in", str(time_left).split(".")[0], end = "\r")
            time.sleep(1)
        print()
        my_daily_queries["value"] = 0
        my_daily_queries["reset_time"] = datetime.datetime.now() + datetime.timedelta(hours = 24)
    
# Function to comply with iNaturalist media download rate limits
def evaluate_media_rate(): 
    # Evaluate size of media downloaded this hour and wait if necessary
    if my_hourly_media["value"] > MAX_MEDIA_PER_HOUR:
        while my_hourly_media["reset_time"] > datetime.datetime.now() :
            time_left = my_hourly_media["reset_time"] - datetime.datetime.now()
            print("WARNING : iNaturalist hourly media download limit reached, download will resume in", str(time_left).split(".")[0], end = "\r")
            time.sleep(1)
        print()
        my_hourly_media["value"] = 0
        my_hourly_media["reset_time"] = datetime.datetime.now() + datetime.timedelta(hours = 1)
    
    # Evaluate size of media downloaded this day and wait if necessary
    if my_daily_media["value"] > MAX_MEDIA_PER_DAY:
        while my_daily_media["reset_time"] > datetime.datetime.now() :
            time_left = my_daily_media["reset_time"] - datetime.datetime.now()
            print("WARNING : iNaturalist daily media download limit reached, download will resume in", str(time_left).split(".")[0], end = "\r")
            time.sleep(1)
        print()
        my_daily_media["value"] = 0
        my_daily_media["reset_time"] = datetime.datetime.now() + datetime.timedelta(hours = 24)

# Function to download images and metadata from a set of observations
def download(my_species_name, observations, image_size) :

    global current_observations_number
    global current_images_number
    global current_dataset_size

    # Run through all observations
    for observation in observations:

        # Get observation information
        species_name = observation["taxon"]["name"]
        observation_id = observation["id"]
        observation_license = observation["license_code"]
        if not observation_license :
            observation_license = "none"
        observer_login = observation["user"]["login"]
        observation_quality = observation["quality_grade"]
        if not observation_quality :
            observation_quality = "none"
        observation_date = observation["observed_on"]
        if not observation_date :
            observation_date = "none"
        if observation["geojson"] :
            observation_latitude = observation["geojson"]["coordinates"][1]
            if not observation_latitude :
                observation_latitude = "none"
            observation_longitude = observation["geojson"]["coordinates"][0]
            if not observation_longitude :
                observation_longitude = "none"
        else : 
            observation_latitude = "none"
            observation_longitude = "none"

        current_observations_number = current_observations_number + 1
        print(f"INFO : {my_species_name} - Observation {current_observations_number}/{max_observations_number} (ID : {observation_id})")

        # Write observation information in the CSV file
        with open("results/" + my_species_name.replace(" ", "_") + "_metadata" + ".csv", 'a', newline = '') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([
                species_name,
                observation_id,
                observation_license,
                observer_login,
                observation_quality,
                observation_date,
                observation_latitude,
                observation_longitude
            ])

        # Run through all images in the observation
        for photo_id in range(len(observation["photos"])):

            # Get image url and replace image size
            image_url = observation["photos"][photo_id]["url"]
            image_url = image_url.replace("/square", f"/{image_size}")
            
            # Create image file path
            file_name = f"{species_name.replace(' ','-')}_{observer_login}_{observation_license}_{observation_id}_{photo_id}.jpeg"
            file_path = os.path.join("results/" + my_species_name.replace(" ", "_") + "_images", file_name)

            # Download image
            image_response = session.get(image_url)
            if image_response.status_code == 200:
                with open(file_path, "wb") as image_file:
                    image_file.write(image_response.content)
                    current_images_number = current_images_number + 1
                    current_dataset_size = current_dataset_size + len(image_response.content)/1000000
                    print(f"INFO : {current_images_number} images downloaded ({round(current_dataset_size, 2)} MB)")

                    # Update user query information
                    my_hourly_media["value"] = my_hourly_media["value"] + len(image_response.content)/1000000000 
                    my_daily_media["value"] = my_daily_media["value"] + len(image_response.content)/1000000000
                    evaluate_media_rate()

            else : 
                print(f"WARNING : Couldn't download image at {image_url}")
    return observation_id

def main():

    global max_observations_number
    global current_observations_number
    global current_images_number
    global current_dataset_size

    # Set configuration according to command line arguments
    parser = argparse.ArgumentParser(description = "Download images from iNaturalist")
    parser.add_argument("-o", "--observations", default = 200, type = int, help = "Number of observations to download per species")
    parser.add_argument("-q", "--quality", default = "research", choices = ["research", "any"], help = "Observations quality grade (research or any)")
    parser.add_argument("-s", "--size", default = "medium", choices = ["small", "medium", "large", "original"], help = "Images size (small, medium, large, original)")
    parser.add_argument("-l", "--license", default = "any", help = "License(s) to consider (any, cc-by, cc-by-nc, cc-by-nc-nd, cc-by-nc-sa, cc-by-nd, cc-by-sa, cc0")
    args = parser.parse_args()

    print()
    print("-------------------------- SCRIPT STARTED --------------------------")
    print()

    # Read CSV file with species names and start ids
    my_species = []
    if os.path.exists("species.csv"):
        with open("species.csv", "r") as species_file:
            species_reader = csv.DictReader(species_file, delimiter = ",")
            for row in species_reader:
                if row["name"] not in [species["name"] for species in my_species] : # Avoid species duplication
                    my_species.append(row)
    else :
        print("ERROR : species.csv file not found")
        print()
        print("------------------- SCRIPT TERMINATED WITH ERROR -------------------")
        print()
        return
    # Create a results folder 
    os.makedirs("results", exist_ok=True)

    # For each species, create a folder for images and a CSV file for observations metadata
    for species in my_species:
        images_folder = "results/" + species["name"].replace(" ", "_") + "_images"
        os.makedirs(images_folder, exist_ok = True)
        metadata_file = "results/" + species["name"].replace(" ", "_") + "_metadata" + ".csv"

        if not os.path.exists(metadata_file):
            with open(metadata_file, 'w', newline = '') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([
                'species_name',
                'observation_id',
                'observation_license',
                'observer_login',
                'observation_quality',
                'observation_date',
                'observation_latidude',
                'observation_longitude'
        ])
        else : 
            print(f"WARNING : {metadata_file} already exists, data will be appended to the existing file")

    # Run through all species 
    for species in my_species:

        # Reset run parameters 
        current_observations_number = 0
        current_images_number = 0
        current_dataset_size = 0
        id_above = species["start_id"]
 
        # Get total number of observations available for the species
        try :
            response = session.get(f"https://api.inaturalist.org/v1/observations?"
                                    f"taxon_name={species['name']}"
                                    f"&quality_grade={args.quality}"
                                    f"&has[]=photos"
                                    f"&license={args.license}"
                                    f"&photo_license={args.license}"
                                    f"&page=1&per_page=1"
                                    f"&order_by=id&order=asc&id_above={id_above}") 
            
            my_daily_queries["value"] = my_daily_queries["value"] + 1

            if response.json()["total_results"] < args.observations :
                print(f"WARNING : Only {response.json()['total_results']} observations available for {species['name']}")
                print(f"INFO : Starting downloading of {response.json()['total_results']} observations for {species['name']}")
                max_observations_number = response.json()["total_results"]
            else :
                print(f"INFO : Starting download of {args.observations} observations for {species['name']}")
                max_observations_number = args.observations

            # Fetch observations for the species
            while current_observations_number < max_observations_number :
                response = session.get(f"https://api.inaturalist.org/v1/observations?"
                                        f"taxon_name={species['name']}"
                                        f"&quality_grade={args.quality}"
                                        f"&has[]=photos"
                                        f"&license={args.license}"
                                        f"&photo_license={args.license}"
                                        f"&page=1&per_page={min(200, max_observations_number - current_observations_number)}"
                                        f"&order_by=id&order=asc&id_above={id_above}") 
                
                time.sleep(1.2) # Delay to avoid overloading the server
                my_daily_queries["value"] = my_daily_queries["value"] + 1
                evaluate_query_rate()

                # Download images and metadata of the observations
                observations = response.json()["results"]
                id_above = download(species['name'], observations, args.size)

            print(f"INFO : Images and metadata download for {species['name']} finished")
        except requests.exceptions.RequestException :
            print("ERROR : Connection error, please check your internet connection and try again")
            print()
            print("------------------- SCRIPT TERMINATED WITH ERROR -------------------")
            print()
            return
        except FileNotFoundError as e :
            print("ERROR : ", e.strerror, ":", e.filename)
            print()
            print("------------------- SCRIPT TERMINATED WITH ERROR -------------------")
            print()
            return

    print()
    print("------------------ SCRIPT TERMINATED SUCCESSFULLY ------------------")
    print()

if __name__ == "__main__":
    main()