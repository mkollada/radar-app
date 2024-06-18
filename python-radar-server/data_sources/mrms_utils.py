# mrms_utils.py
import os
import requests
import logging
from bs4 import BeautifulSoup
import datetime

def download_file(url, directory, filename):
    logging.info(f"Starting download of file from {url}")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        filepath = os.path.join(directory, filename)
        logging.info(f"Writing file to {filepath}")
        try:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            logging.info(f"Successfully downloaded file to {filepath}")
        except IOError as e:
            logging.error(f"Failed to write file {filepath}: {e}")
            raise
        return filepath
    else:
        logging.error(f"Failed to download file from {url}, status code: {response.status_code}")
        raise Exception(f"Failed to download file from {url}")

def fetch_and_download_mrms_data(base_url, subdir_path, subdir):
    # Send a request to the URL
    response = requests.get(base_url)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve data: {response.status_code}")

    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all links on the page
    links = soup.find_all('a')
    
    # Filter and sort the file links by date
    file_links = []
    for link in links:
        href = link.get('href')
        if href.endswith('.gz') and 'latest' not in href:
            try:
                # Extract date from the filename
                parts = href.split('_')
                date_part = parts[-1].split('.')[0]  # Extract the date and time part
                file_date = datetime.datetime.strptime(date_part, '%Y%m%d-%H%M%S')
                file_links.append((href, file_date))
            except (IndexError, ValueError) as e:
                logging.error(f"Error parsing date from {href}: {e}")

    # Sort the links by date
    file_links.sort(key=lambda x: x[1])

    # Select the last 4 files
    recent_file_links = file_links[-4:]

    downloaded_files = []

    # Always download the 'latest' file
    latest_file_url = f"{base_url}MRMS_{subdir}.latest.grib2.gz"
    latest_filename = f"MRMS_{subdir}.latest.grib2.gz"
    latest_grib_file_path = download_file(latest_file_url, subdir_path, latest_filename)
    downloaded_files.append(latest_grib_file_path)

    # Download the selected files
    for file_link, _ in recent_file_links:
        file_url = base_url + file_link
        filename = file_link
        file_path = download_file(file_url, subdir_path, filename)
        downloaded_files.append(file_path)

    return downloaded_files
