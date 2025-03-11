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
    
    # Find all elements containing the filter value text
    # filter_elements = []
    
    # # Method 1: Find elements with exact text match
    # for element in soup.find_all(string=re.compile(f"^{re.escape(filter_value)}$")):
    #     parent = element.parent
    #     filter_elements.append({
    #         'element_type': parent.name,
    #         'element_text': element.strip(),
    #         'element_html': str(parent),
    #         'element_attrs': parent.attrs
    #     })
    
    # # Method 2: Find elements with text match with possible whitespace
    # for element in soup.find_all(string=re.compile(f"^\s*{re.escape(filter_value)}\s*$")):
    #     parent = element.parent
    #     filter_elements.append({
    #         'element_type': parent.name,
    #         'element_text': element.strip(),
    #         'element_html': str(parent),
    #         'element_attrs': parent.attrs
    #     })
    
    # # Method 3: Find input elements that have filter value in their label or nearby text
    # for label in soup.find_all(['label', 'div'], string=re.compile(re.escape(filter_value))):
    #     # Look for nearby input elements (children, siblings, etc.)
    #     inputs = label.find_all('input') or label.parent.find_all('input')
    #     for input_elem in inputs:
    #         filter_elements.append({
    #             'element_type': 'input',
    #             'element_text': 'Input near: ' + label.get_text().strip(),
    #             'element_html': str(input_elem),
    #             'element_attrs': input_elem.attrs
    #         })
    
    # # Remove duplicates based on element HTML
    # unique_elements = []
    # seen_html = set()
    # for elem in filter_elements:
    #     if elem['element_html'] not in seen_html:
    #         unique_elements.append(elem)
    #         seen_html.add(elem['element_html'])
    
    # filter_elements = unique_elements
    # print(f"Found {len(filter_elements)} potential elements for {filter_type}={filter_value}")
    
    # if not filter_elements:
    #     print(f"No elements found for {filter_type}={filter_value}, skipping this filter")
    #     return
    
    # # Create system and user prompts for GPT-4o
    # system_prompt = f"""
    # You are an expert in web automation. Analyze both the screenshot of a Kayak flight search page 
    # and the HTML elements I've extracted that contain "{filter_value}" references.
    
    # Your task is to identify the most reliable selector that can be used with Selenium to click 
    # on the {filter_type} filter for {filter_value} in the filters section.
    
    # Examine both the visual information from the screenshot and the HTML structure from the extracted elements.
    # Return ONLY the most reliable selector as a JSON object with these keys:
    # - 'selector_type': either 'xpath', 'css', or 'id'
    # - 'selector': the actual selector string
    # - 'explanation': brief explanation of why this is the best selector
    # """
    
    # # Format the HTML elements for the prompt
    # html_elements_text = f"Extracted HTML elements containing '{filter_value}':\n\n"
    # for i, elem in enumerate(filter_elements, 1):
    #     html_elements_text += f"Element {i}:\n"
    #     html_elements_text += f"Type: {elem['element_type']}\n"
    #     html_elements_text += f"Text: {elem['element_text']}\n"
    #     html_elements_text += f"Attributes: {elem['element_attrs']}\n"
    #     html_elements_text += f"HTML: {elem['element_html'][:200]}...\n\n"
    
    # user_prompt = f"""
    # Find the {filter_type} filter for "{filter_value}" in the Kayak flight search page.
    
    # Here are HTML elements containing '{filter_value}' references:
    
    # {html_elements_text}
    
    # The screenshot shows the filters section of the page. Please analyze both the HTML elements and the screenshot 
    # to provide the most reliable selector for clicking the {filter_type} filter for {filter_value}.
    # """
    
    # gpt_response = openai_req_generator(
    #     system_prompt, 
    #     user_prompt, 
    #     files=[screenshot_path], 
    #     json_output=True, 
    #     model_name="gpt-4o"
    # )

    # # try:
    # if isinstance(gpt_response, str):
    #     gpt_response = json.loads(gpt_response)
    
    # print(gpt_response)
    # # Extract selector information
    # selector_type = gpt_response.get('selector_type', 'xpath')
    # selector = gpt_response.get('selector', '')
    # explanation = gpt_response.get('explanation', '')

    selector_type = 'id'
    selector = 'valueSetFilter-vertical-airlines-AC-label'

    print(f"Using {selector_type} selector: {selector}")
    # print(f"Explanation: {explanation}")
    
    # Click on the filter
    wait = WebDriverWait(driver, 40)  # Increase timeout to 10 seconds
    try:
        # Check if the label element exists and is visible
        element_exists = driver.execute_script(f"return !!document.getElementById('{selector}') && document.getElementById('{selector}').offsetParent !== null")
        # Click on the label instead of the checkbox
        driver.execute_script(f"document.getElementById('{selector}').click();")
        print(f"Successfully clicked on label for {filter_type} filter: {filter_value}")
    except TimeoutException:
        print(f"Timeout finding element with selector {selector_type}: {selector}")
        # Implement fallback methods that were previously commented out
        try:
            # Generic fallback methods that work for most filter types
            fallback_methods = [
                f"//span[contains(text(), '{filter_value}')]/ancestor::label//input[@type='checkbox']",
                f"//label[contains(., '{filter_value}')]//input",
                f"//div[contains(., '{filter_value}')]//input[@type='checkbox']",
                f"//*[contains(text(), '{filter_value}')]/ancestor::*[input[@type='checkbox']]//input"
            ]
            
            for method in fallback_methods:
                try:
                    elements = driver.find_elements(By.XPATH, method)
                    if elements:
                        driver.execute_script("arguments[0].click();", elements[0])
                        print(f"Clicked {filter_type} filter using fallback method: {method}")
                        time.sleep(5)
                        break
                except Exception:
                    continue
        except Exception as fallback_error:
            print(f"All fallback methods failed: {str(fallback_error)}")
    
    # Wait for results to update
    time.sleep(30)  # Increase wait time after applying filter
    # except Exception as e:
    #     print(e)
    #     print(f"Error applying {filter_type} filter for {filter_value}: {str(e)}")
    #     # Fallback: try a more generic approach
    #     try:
    #         # Generic fallback methods that work for most filter types
    #         fallback_methods = [
    #             f"//span[contains(text(), '{filter_value}')]/ancestor::label//input[@type='checkbox']",
    #             f"//label[contains(., '{filter_value}')]//input",
    #             f"//div[contains(., '{filter_value}')]//input[@type='checkbox']",
    #             f"//*[contains(text(), '{filter_value}')]/ancestor::*[input[@type='checkbox']]//input"
    #         ]
            
    #         for method in fallback_methods:
    #             try:
    #                 elements = driver.find_elements(By.XPATH, method)
    #                 if elements:
    #                     driver.execute_script("arguments[0].click();", elements[0])
    #                     print(f"Clicked {filter_type} filter using fallback method: {method}")
    #                     time.sleep(5)
    #                     break
    #             except Exception:
    #                 continue
    #     except Exception as fallback_error:
    #         print(f"All fallback methods failed: {str(fallback_error)}")


# Apply multiple filters
filters = {
    'airline': 'Air Canada'
    # 'stops': 'nonstop'
}


crawl_flight_data_kayak(search, i, filters)
