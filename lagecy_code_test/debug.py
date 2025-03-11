import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../modules')))


step2_file = 'output/step2_augmented_searches.json'
if os.path.exists(step2_file):
    with open(step2_file, 'r') as f:
        augmented_searches = json.load(f)
    print("Step 2: Loading existing augmented searches from file")

search = augmented_searches[0]
i = 0

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json
import requests
import time
from utils import save_output, openai_req_generator
from selenium.webdriver.chrome.service import Service
import os
from PIL import Image
import io
from bs4 import BeautifulSoup
import re

def crawl_flight_data_kayak(flight_info, i, filters=None):
    """
    Crawl flight data from Kayak with optional filters
    
    Parameters:
    flight_info (dict): Flight search parameters
    i (int): Index for file naming
    filters (dict): Optional filters to apply, e.g. {'airline': 'Air Canada', 'stops': 'nonstop'}
    """
    # Construct Kayak URL with proper format
    base_url = "https://www.kayak.com/flights/"
    
    # Format airports (add 'nearby' suffix for broader search)
    source = f"{flight_info['source_airport'].upper()},nearby"
    destination = f"{flight_info['destination_airport'].upper()},nearby"
    
    # Format date (YYYY-MM-DD)
    date_str = flight_info['start_date']
    
    # Format passengers
    passengers = f"{flight_info['number_of_passengers']}adults"
    
    # Construct URL path
    url_path = f"{source}-{destination}/{date_str}/{passengers}?sort=bestflight_a"
    
    url = base_url + url_path
    # try:
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Add random user agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    homedir = os.path.expanduser("~")
    chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
    webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")

    # Initialize driver
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    
    # Execute CDP commands to modify navigator.webdriver flag
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'})
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print(f"Kayak URL: {url}")
    driver.get(url)
    
    # Handle cookie consent
    try:
        wait = WebDriverWait(driver, 10)
        cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.RxNS')))
        accept_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.RxNS')
        for button in accept_buttons:
            if button.text.strip().lower() == 'accept all':
                button.click()
                print("Accepted cookies")
                break
    except TimeoutException:
        print("Cookie consent button not found or not clickable")
    
    print("Waiting for page to load...")
    time.sleep(10)
    
    # Set window size for consistent screenshots
    driver.set_window_size(1920, 1200)
    
    # Scroll to the filters section (left sidebar)
    driver.execute_script("window.scrollTo(0, 650)")
    time.sleep(2)

    # Save the HTML content of the page
    page_content = driver.page_source
    html_file_path = f'output/step3_images/kayak_page_{i}.html'
    with open(html_file_path, 'w', encoding='utf-8') as html_file:
        html_file.write(page_content)
    print(f"Saved HTML content to {html_file_path}")

    # Take screenshot of the filters section
    filters_screenshot_path = f'output/step3_images/kayak_filters_{i}.png'
    driver.save_screenshot(filters_screenshot_path)
    
    # Enhance screenshot quality
    img = Image.open(filters_screenshot_path)
    img = img.convert('RGB')
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
    img.save(filters_screenshot_path, 'PNG', quality=100, optimize=False)
    
    # Apply filters if provided
    if filters and isinstance(filters, dict):
        for filter_type, filter_value in filters.items():
            apply_filter(driver, filter_type, filter_value, html_file_path, filters_screenshot_path)
            # Wait between applying filters
            time.sleep(3)
    
    # Get total page height after filtering
    return
    total_height = driver.execute_script("return document.body.scrollHeight")
    
    # Create output directory
    os.makedirs('output/step3_images', exist_ok=True)
    
    # Screenshot parameters
    viewport_height = 1000
    overlap = 100
    current_position = 0
    section = 0
    
    # Take screenshots of filtered results
    while current_position < total_height:
        driver.execute_script(f"window.scrollTo(0, {current_position})")
        time.sleep(2)
        
        screenshot_path = f'output/step3_images/kayak_results_{i}_section_{section + 1}.png'
        driver.save_screenshot(screenshot_path)
        
        # Enhance screenshot quality
        img = Image.open(screenshot_path)
        img = img.convert('RGB')
        img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
        img.save(screenshot_path, 'PNG', quality=100, optimize=False)
        
        print(f"Captured section {section + 1} at position {current_position}/{total_height}")
        
        current_position += (viewport_height - overlap)
        section += 1
    
    driver.quit()
    return f'output/step3_images/kayak_results_{i}_section_*.png'
        
    # except Exception as e:
    #     print(f"Error crawling Kayak: {str(e)}")
    #     if 'driver' in locals():
    #         driver.quit()
    #     return None

def apply_filter(driver, filter_type, filter_value, html_file_path, screenshot_path):
    """Apply a single filter to the search results"""
    print(f"Applying filter: {filter_type}={filter_value}")
    
    # Extract potential filter elements from HTML
    with open(html_file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # For Air Canada specifically, we know the exact ID from inspection
    if filter_type == 'airline' and filter_value == 'Air Canada':
        try:
            # First try to find the input element directly by ID
            print("Looking for Air Canada checkbox by ID")
            checkbox_id = "valueSetFilter-vertical-airlines-AC"
            
            # Use JavaScript to check if element exists and is visible
            element_exists = driver.execute_script(f"return !!document.getElementById('{checkbox_id}') && document.getElementById('{checkbox_id}').offsetParent !== null")
            
            if element_exists:
                # Click using JavaScript which bypasses visibility issues
                driver.execute_script(f"document.getElementById('{checkbox_id}').click();")
                print("Successfully clicked Air Canada checkbox using JavaScript")
                time.sleep(20)
                return
            else:
                print(f"Element with ID {checkbox_id} not found or not visible")
                
            # If direct ID approach fails, try clicking the label instead
            print("Trying to click on the Air Canada label")
            label_xpath = "//div[contains(@class, 'hYzH-checkbox-label') and text()='Air Canada']"
            labels = driver.find_elements(By.XPATH, label_xpath)
            
            if labels:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", labels[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", labels[0])
                print("Successfully clicked on Air Canada label")
                time.sleep(5)
                return
            else:
                print("Air Canada label not found")
        except Exception as e:
            print(f"Error targeting Air Canada checkbox: {str(e)}")
    
    # Generic approach for other filters or as fallback
    try:
        # Try finding by text content in the label
        xpath = f"//div[contains(text(), '{filter_value}')]"
        elements = driver.find_elements(By.XPATH, xpath)
        
        if elements:
            # Found the text element, now click it
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elements[0])
            time.sleep(1)
            driver.execute_script("arguments[0].click();", elements[0])
            print(f"Successfully clicked on {filter_value} text element")
            time.sleep(5)
            return
        else:
            print(f"No elements found containing text '{filter_value}'")
            
        # Last resort: try to find any checkbox near text containing the filter value
        xpath = f"//*[contains(text(), '{filter_value}')]/ancestor::*[.//input[@type='checkbox']]//input[@type='checkbox']"
        checkboxes = driver.find_elements(By.XPATH, xpath)
        
        if checkboxes:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkboxes[0])
            time.sleep(1)
            driver.execute_script("arguments[0].click();", checkboxes[0])
            print(f"Successfully clicked on checkbox near '{filter_value}'")
            time.sleep(5)
            return
        else:
            print(f"No checkboxes found near text '{filter_value}'")
            
    except Exception as e:
        print(f"All methods failed to apply {filter_type} filter for {filter_value}: {str(e)}")


# Apply multiple filters
filters = {
    'airline': 'Air Canada'
    # 'stops': 'nonstop'
}


crawl_flight_data_kayak(search, i, filters)
