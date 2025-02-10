from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import requests
import time
from .utils import save_output
from selenium.webdriver.chrome.service import Service
import os


def crawl_flight_data_skyscanner(flight_info):
    base_url = "https://www.skyscanner.com/transport/flights/"
    params = {
        "adults": str(flight_info['number_of_passengers']),
        "adultsv2": str(flight_info['number_of_passengers']),
        "cabinclass": flight_info.get('other_data', {}).get('class', 'economy').lower()
    }
    
    # Construct URL path with airports and dates
    url_path = (
        f"{flight_info['source_airport'].lower()}/"
        f"{flight_info['destination_airport'].lower()}/"
        f"{flight_info['start_date'].replace('-','')}/"
    )
    
    if flight_info['return_date'] and flight_info['return_date'] != '-':
        url_path += f"{flight_info['return_date'].replace('-','')}/"
        
    url = base_url + url_path
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--headless")

        homedir = os.path.expanduser("~")
        chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
        webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")

        # Choose Chrome Browser
        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
                
        final_url = requests.Request('GET', url, params=params).prepare().url
        print(f"Skyscanner URL: {final_url}")
        driver.get(final_url)
        
        print("Waiting for page to load...")
        time.sleep(30)
        
        page_content = driver.page_source
        print("Page content captured")
        
        if page_content:
            save_output(
                page_content,
                'skyscanner_results.html',
            )
             
        driver.quit()
        return page_content
        
    except Exception as e:
        print(f"Error crawling Skyscanner: {str(e)}")
        return None

def crawl_flight_data_flytoday(flight_info):
    # Convert the JSON string to a dictionary if it's a string
    if isinstance(flight_info, str):
        flight_info = json.loads(flight_info)
    
    # Rest of the crawling code remains the same
    # Construct the URL with flight information
    base_url = "https://www.flytodayir.com/flight/search"
    params = {
        "departure": f"{flight_info['source_airport']}",
        "arrival": f"{flight_info['destination_airport']}", 
        "departureDate": flight_info['start_date'],
        "adt": flight_info['number_of_passengers'],
        "chd": "0",
        "inf": "0",
        "cabin": "1",
        "isAnyWhere": "false"
    }
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--headless") # Ensure GUI is off
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Construct and visit the URL
        final_url = requests.Request('GET', base_url, params=params).prepare().url
        print(f"Final URL: {final_url}")
        driver.get(final_url)
        
        # Wait for page to be fully loaded
        print("Waiting for page to load...")
        time.sleep(50)  # Wait 30 seconds for the page to load completely
        
        # Get the page source after waiting
        page_content = driver.page_source
        print("Page content captured")
        
        # Save the HTML response to a file

        if page_content:
            save_output(
                page_content,
                'flight_search_results.html',
            )
             
        driver.quit()
        return page_content
            
    except Exception as e:
        print(f"Error making request: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return None