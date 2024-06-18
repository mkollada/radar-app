# metar_utils.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import datetime
import logging

BASE_CATALOG_URL = "https://thredds.ucar.edu/thredds/catalog/noaaport/text/metar/catalog.html"

def get_metar_files():
    response = requests.get(BASE_CATALOG_URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')
    file_links = [link.get('href') for link in links if link.get('href').endswith('.txt')]
    return file_links

def download_metar_file(file_url):
    response = requests.get(file_url)
    return response.text

def parse_metar_report(report):
    pattern = (
        r"^(?P<type>METAR|SPECI)\s+"
        r"(?P<station>[A-Z]{4})\s+"
        r"(?P<datetime>\d{6}Z)\s+"
        r"(?P<wind>\d{5}KT|VRB\d{2}KT|VRB\d{2}G\d{2}KT|VRB\d{2}\d{2}/\d{2}|AUTO)?\s*"
        r"(?P<visibility>\d{4}|CAVOK)?\s*"
        r"(?P<clouds>.*?)(?=\d{2}/\d{2}|M?\d{2}/M?\d{2})"
        r"(?P<temperature>M?\d{2}/M?\d{2})\s+"
        r"(?P<pressure>A\d{4})\s*"
        r"(?P<remarks>.*)"
    )

    match = re.match(pattern, report)
    if not match:
        logging.error(f"Failed to parse METAR report: {report}")
        return None

    data = match.groupdict()

    datetime_str = data['datetime']
    day = int(datetime_str[:2])
    hour = int(datetime_str[2:4])
    minute = int(datetime_str[4:6])
    data['datetime'] = datetime.datetime.utcnow().replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)

    temp_dew = data['temperature'].split('/')
    data['temperature'] = int(temp_dew[0].replace('M', '-'))
    data['dew_point'] = int(temp_dew[1].replace('M', '-'))

    return data

def get_metar_data(max_files=5):
    file_links = get_metar_files()

    # Sort files by most recent
    file_links.sort(reverse=True)

    # Limit to max_files
    file_links = file_links[:max_files]

    all_reports = []

    for file_link in file_links:
        print(f"Processing file: {file_link}")
        file_content = download_metar_file(file_link)
        reports = file_content.strip().split('\n\n')  # Assuming each document is separated by double newline
        for report in reports:
            report = report.strip().replace('\n', ' ')  # Combine lines of a single report
            parsed_data = parse_metar_report(report)
            if parsed_data:
                all_reports.append(parsed_data)

    df = pd.DataFrame(all_reports)
    return df
