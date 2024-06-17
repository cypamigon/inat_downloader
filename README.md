# inat_downloader

inat_downloader is a Python script for bulk downloading images and metadata from [iNaturalist.org](https://www.inaturalist.org/ "iNaturalist's Homepage") observations. Selected observations are based on a user-specified list of species. 

## Installation


1. Install the required Python package : 
```
pip install requests
```
2. Clone the repository : 
```
git clone https://github.com/cypamigon/inat_downloader.git
```
3. Change your current working directory to the downloaded folder : 
```
cd inat_downloader
```

## Usage 

1. Prepare a CSV file named `species.csv` containing the scientific name of the species for which you want to download images and metadata. You also need to associate a start ID for each species. The CSV file must have the following structure :

| name,start_id       |
|---------------------|
|Apis mellifera,0     |
|Mantis religiosa,0   |
|Martes americana,0   |

An example of such a file is provided in the repository.

The start ID is the ID of iNaturalist's observation from which you want to start downloading images. This is useful if something went wrong during a previous download and you want to restart from where it stopped. If you want to start downloading from the first species observation, just put '0' as start ID.

2. Run the script : 

```
python inat_downloader.py [-o OBSERVATIONS] [-q QUALITY] [-l LICENSE] [-s SIZE] 
``` 

The script accepts the following arguments :

`-o` `--observations` : Number of observations to download per species. Default : **_200_**  
`-q` `--quality` : Quality of the observations (**_research_** or **_any_**). Default : **_research_**  
`-l` `--license` : License(s) of the observations and photos to consider  (**_any_**, **_cc-by_**, **_cc-by-nc_**, **_cc-by-nd_**, **_cc-by-sa_**, **_cc-by-nc-nd_**, **_cc-by-nc-sa_**, **_cc0_**). Default : **_any_**  
`-s` `--size` : Size of the images downloaded (**_small_**, **_medium_**, **_large_**, **_original_**). Default : **_medium_**  
* Small :  maximum 240px on the longest side.
* Medium : maximum 500px on the longest side.
* Large : maximum 1024px on the longest side.
* Original : maximum 2048px on the longest side.  


**Example :**
```
python inat_downloader.py -o 5000 -q research -l cc-by,cc-by-nc,cc0 -s large
```
This would download, for each species, large images and metadata from 5000 research-grade observations. Only observations with cc-by, cc-by-nc and cc0 licenses will be considered.

**Expected output :**

In your terminal, you should see something like this : 

``` 
-------------------------- SCRIPT STARTED --------------------------

INFO : Starting download of 5000 observations for Apis mellifera
INFO : Apis mellifera - Observation 1/5000 (ID : 6093)
INFO : 1 images downloaded (0.05 MB)
INFO : 2 images downloaded (0.12 MB)
INFO : 3 images downloaded (0.18 MB)
INFO : Apis mellifera - Observation 2/5000 (ID : 7505)
INFO : 4 images downloaded (0.57 MB)
INFO : 5 images downloaded (1.01 MB)
INFO : Apis mellifera - Observation 3/5000 (ID : 10000)
INFO : 6 images downloaded (1.11 MB)
INFO : 7 images downloaded (1.2 MB)
```

In a `results` folder, you should find for each species a folder containing the images downloaded and a CSV file containing the associated metadata : species_name, observation_id, observation_license, observer_login, observation_quality, observation_date, observation_latitude and observation_longitude.  
Images are named as follow : `species_user_license_observation-id_photos-in-observation.jpg`. (e.g. `Apis-mellifera_Steve_cc-by-nc-nd_6093_3.jpg`)


## Note

The script relies on the iNaturalist API to download images and metadata. The API limits the request to 60 requests per minute. A delay between each request has been added to the script to comply with this limit. Additionally, the API restricts the downloads to 5 GB per hour and 24 GB per day. If these limits are nearly reached, the script will pause temporarily before resuming the download.

## License 

Distributed under the MIT License. See `LICENSE.txt` for more information.
