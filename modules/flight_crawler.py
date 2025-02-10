from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json
import requests
import time
from .utils import save_output
from selenium.webdriver.chrome.service import Service
import os

def crawl_flight_data_kayak(flight_info):
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
        # Add these new arguments to make the browser appear more human-like
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add random user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

        homedir = os.path.expanduser("~")
        chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
        webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")

        # Choose Chrome Browser
        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        
        # Execute CDP commands to modify navigator.webdriver flag
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'})
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        final_url = requests.Request('GET', url, params=params).prepare().url
        final_url = "https://www.kayak.com/flights/DXB,nearby-YTO,nearby/2025-03-28/3adults"
        print(f"Skyscanner URL: {final_url}")
        driver.get(final_url)
        
        # Wait for and click the cookie consent button
        try:
            # Wait up to 10 seconds for the cookie consent button
            wait = WebDriverWait(driver, 10)
            cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.RxNS')))
            # Find the specific "Accept all" button by its text content
            accept_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.RxNS')
            for button in accept_buttons:
                if button.text.strip().lower() == 'accept all':
                    button.click()
                    print("Accepted cookies")
                    break
        except TimeoutException:
            print("Cookie consent button not found or not clickable")
        
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
        # Add these new arguments to make the browser appear more human-like
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add random user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

        homedir = os.path.expanduser("~")
        chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
        webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")

        # Choose Chrome Browser
        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        
        # Execute CDP commands to modify navigator.webdriver flag
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'})
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        final_url = requests.Request('GET', url, params=params).prepare().url
        final_url = "https://www.kayak.com/flights/DXB,nearby-YTO,nearby/2025-03-28/3adults"
        print(f"Skyscanner URL: {final_url}")
        driver.get(final_url)
        
        # Wait for and click the cookie consent button
        try:
            # Wait up to 10 seconds for the cookie consent button
            wait = WebDriverWait(driver, 35)
            cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test="cookie-policy-dialog-accept"]')))
            cookie_button.click()
            print("Accepted cookies")
        except TimeoutException:
            print("Cookie consent button not found or not clickable")
        
        print("Waiting for page to load...")
        time.sleep(20)
        
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